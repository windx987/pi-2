# Checks for exercise 05, one or more per step of README.md. Run: python3 exercises/check.py 05
#
# A fake model replays prepared answers, so no model is needed: the subagent calls the echo tool once,
# then answers.

import re
import shutil
import tempfile
import unittest

from check import NotDone, call, error_of, load_tool

from pi2 import ExtensionAPI, ToolContext, define_tool
from pi2.model_runtime import ModelRuntime
from pi2.session import AgentSession

ECHO = define_tool(
    name="echo", label="echo", description="Echo text",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    execute=lambda params, ctx: f"echo: {params['text']}",
)


def answer(*blocks, stop_reason="stop", **extra):
    return {"role": "assistant", "content": list(blocks), "stop_reason": stop_reason,
            "usage": {"input": 1500, "output": 20}, **extra}


TOOL_CALL = answer({"type": "toolCall", "id": "c1", "name": "echo", "arguments": {"text": "x"}}, stop_reason="tool_use")
FINAL = answer({"type": "text", "text": "Found 3 files."})


class SubagentTest(unittest.TestCase):
    def setUp(self):
        self.subagent = load_tool("subagent")
        self.requests = []  # (messages, tool names) of every request the subagent sends
        self.agent_dir = tempfile.mkdtemp(prefix="pi2-check-")  # the sessions save their files here
        self.addCleanup(shutil.rmtree, self.agent_dir, ignore_errors=True)

    def parent(self, *answers):
        """A parent session with echo and subagent, whose model replays answers."""
        queue = list(answers)

        def stream_fn(model, context):
            self.requests.append(([dict(m) for m in context["messages"]], [t.name for t in context["tools"]]))
            message = queue.pop(0)
            if message == "interrupt":
                raise KeyboardInterrupt
            yield {"type": "done", "message": message}

        runtime = ModelRuntime(self.agent_dir)
        runtime.stream_fn = stream_fn
        extensions = ExtensionAPI()
        extensions.register_tool(ECHO)
        extensions.register_tool(self.subagent)
        session = AgentSession(runtime, {"id": "fake"}, extensions, "/work", self.agent_dir)
        session.messages.append({"role": "user", "content": "the parent's own conversation"})
        return session

    def run_task(self, *answers):
        session = self.parent(*answers)
        return call(self.subagent, {"task": "List the files."}, "/work", session=session), session

    def test_1_tools(self):
        """Step 1: the subagent gets the parent's tools, except subagent itself."""
        self.run_task(TOOL_CALL, FINAL)
        tools = self.requests[0][1]
        self.assertIn("echo", tools, f"the subagent should get the parent's tools: {tools}")
        self.assertNotIn("subagent", tools, "a subagent must not start another one")

    def test_1_parent_keeps_its_tools(self):
        """Step 1: the parent still has subagent afterwards (register on a new ExtensionAPI)."""
        _, session = self.run_task(TOOL_CALL, FINAL)
        self.assertIn("subagent", session.extensions.tools)

    def test_2_own_context(self):
        """Step 2: the subagent starts with an empty context: only the task, not the parent's messages."""
        _, session = self.run_task(TOOL_CALL, FINAL)
        first = self.requests[0][0]
        self.assertEqual([m["role"] for m in first], ["user"], "the subagent's first request has one message")
        self.assertEqual(first[0]["content"], "List the files.")
        self.assertEqual(len(session.messages), 1, "the subagent's messages must not land in the parent")

    def test_2_runs_its_tools(self):
        """Step 2: the subagent's loop runs its tool calls and asks again."""
        self.run_task(TOOL_CALL, FINAL)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(self.requests[1][0][-1]["content"], "echo: x")

    def test_4_answer(self):
        """Step 4: the result is the subagent's final answer."""
        result, _ = self.run_task(TOOL_CALL, FINAL)
        self.assertIn("Found 3 files.", result)

    def test_4_cost_note(self):
        """Step 4: a note says what it cost: 1 tool call, and the input tokens (3.0k)."""
        result, _ = self.run_task(TOOL_CALL, FINAL)
        note = result.replace("Found 3 files.", "")
        self.assertRegex(note, re.compile(r"\b1\b\D{0,12}tool|tool\D{0,12}\b1\b", re.IGNORECASE), f"say it made 1 tool call: {result!r}")
        self.assertRegex(note, r"3\.0\s*k|3000|3,000", f"say it used 3000 input tokens (3.0k): {result!r}")

    def test_3_error(self):
        """Step 3: when the subagent's model fails, the tool raises with its error message."""
        failed = answer(stop_reason="error", error_message="502 Bad Gateway")
        error = error_of(self.subagent, {"task": "List the files."}, "/work", session=self.parent(failed))
        self.assertIn("502 Bad Gateway", str(error))

    def test_3_aborted(self):
        """Step 3: ctrl+c in the subagent raises KeyboardInterrupt, so the parent stops too."""
        session = self.parent("interrupt")
        try:
            result = self.subagent.execute({"task": "List the files."}, ToolContext(cwd="/work", session=session))
        except NotImplementedError as error:
            raise NotDone(str(error)) from None
        except KeyboardInterrupt:
            return
        except Exception as error:  # noqa: BLE001
            self.fail(f"raise KeyboardInterrupt, not {type(error).__name__}: {error}")
        self.fail(f"raise KeyboardInterrupt instead of returning {result!r}")
