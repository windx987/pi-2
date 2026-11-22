# Checks for exercise 06, one or more per step of 06-subagents.md. Run: python3 exercises/check.py 06
#
# A fake model replays prepared answers, so no model is needed: the subagent calls echo once, then
# answers.

import re

from check import NotDone, Workspace, call, error_of, load_tool

from pi2 import ExtensionAPI, ToolContext, define_tool
from pi2.session import AgentSession

ECHO = define_tool(
    name="echo",
    label="echo",
    description="Echo text",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    execute=lambda params, ctx: f"echo: {params['text']}",
)


def answer(*blocks, stop_reason="stop", **extra):
    return {
        "role": "assistant",
        "content": list(blocks),
        "stop_reason": stop_reason,
        "usage": {"input": 1500, "output": 20},
        **extra,
    }


TOOL_CALL = answer({"type": "toolCall", "id": "c1", "name": "echo", "arguments": {"text": "x"}}, stop_reason="tool_use")
FINAL = answer({"type": "text", "text": "Found 3 files."})


class FakeRuntime:
    """Replays prepared answers, one per request."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.requests = []  # (messages, tool names) of every request the subagent sends

    def stream_fn(self, model, context):
        self.requests.append(([dict(m) for m in context["messages"]], [t.name for t in context["tools"]]))
        answer = self.answers.pop(0)
        if answer == "interrupt":
            raise KeyboardInterrupt
        yield {"type": "done", "message": answer}


class SubagentTest(Workspace):
    def setUp(self):
        super().setUp()
        self.subagent = load_tool("subagent")
        self.agent_dir = self.cwd / "agent"
        self.agent_dir.mkdir()
        self.model = {"id": "fake", "context_window": 32768}

    def parent(self, *answers):
        """A parent session with echo and subagent, whose model replays answers."""
        runtime = FakeRuntime(answers)
        extensions = ExtensionAPI()
        extensions.register_tool(ECHO)
        extensions.register_tool(self.subagent)
        session = AgentSession(runtime, self.model, extensions, str(self.cwd), self.agent_dir)
        session.messages.append({"role": "user", "content": "the parent's own conversation"})
        return session, runtime

    def run_task(self, *answers):
        session, runtime = self.parent(*answers)
        result = call(self.subagent, {"task": "List the files."}, self.cwd, session=session)
        return result, session, runtime

    def test_1_tools(self):
        """Step 1: the subagent gets the parent's tools, except subagent itself."""
        _, _, runtime = self.run_task(TOOL_CALL, FINAL)
        tools = runtime.requests[0][1]
        self.assertIn("echo", tools, f"the subagent should get the parent's tools: {tools}")
        self.assertNotIn("subagent", tools, "a subagent must not start another one")

    def test_1_parent_keeps_its_tools(self):
        """Step 1: the parent still has subagent afterwards."""
        _, session, _ = self.run_task(TOOL_CALL, FINAL)
        self.assertIn("subagent", session.extensions.tools)

    def test_2_own_context(self):
        """Step 2: the subagent starts with an empty context: only the task, not the parent's messages."""
        _, session, runtime = self.run_task(TOOL_CALL, FINAL)
        first = runtime.requests[0][0]
        self.assertEqual([m["role"] for m in first], ["user"], "the subagent's first request has one message")
        self.assertEqual(first[0]["content"], "List the files.")
        self.assertEqual(len(session.messages), 1, "the subagent's messages must not land in the parent")

    def test_2_runs_its_tools(self):
        """Step 2: the subagent's loop runs its tool calls and asks again."""
        _, _, runtime = self.run_task(TOOL_CALL, FINAL)
        self.assertEqual(len(runtime.requests), 2)
        self.assertEqual(runtime.requests[1][0][-1]["content"], "echo: x")

    def test_4_answer(self):
        """Step 4: the result is the subagent's final answer."""
        result, _, _ = self.run_task(TOOL_CALL, FINAL)
        self.assertIn("Found 3 files.", result)

    def test_4_cost_note(self):
        """Step 4: a note says what it cost: 1 tool call and the input tokens (3.0k)."""
        result, _, _ = self.run_task(TOOL_CALL, FINAL)
        note = result.replace("Found 3 files.", "")
        self.assertRegex(
            note,
            re.compile(r"\b1\b\D{0,12}tool|tool\D{0,12}\b1\b", re.IGNORECASE),
            f"say it made 1 tool call: {result!r}",
        )
        self.assertRegex(note, r"3\.0\s*k|3000|3,000", f"say it used 3000 input tokens (3.0k): {result!r}")

    def test_3_error(self):
        """Step 3: when the subagent's model fails, the tool raises with its error message."""
        failed = answer(stop_reason="error", error_message="502 Bad Gateway")
        session, _ = self.parent(failed)
        error = error_of(self.subagent, {"task": "List the files."}, self.cwd, session=session)
        self.assertIn("502 Bad Gateway", str(error))

    def test_3_aborted(self):
        """Step 3: ctrl+c in the subagent raises KeyboardInterrupt, so the parent stops too."""
        session, _ = self.parent("interrupt")
        try:
            result = self.subagent.execute(
                {"task": "List the files."}, ToolContext(cwd=str(self.cwd), session=session)
            )
        except NotImplementedError as error:
            raise NotDone(str(error)) from None
        except KeyboardInterrupt:
            return
        except Exception as error:  # noqa: BLE001
            self.fail(f"raise KeyboardInterrupt, not {type(error).__name__}: {error}")
        self.fail(f"raise KeyboardInterrupt instead of returning {result!r}")

    def test_no_session(self):
        """A subagent needs a running session."""
        error_of(self.subagent, {"task": "List the files."}, self.cwd)

    def test_empty_task(self):
        """An empty task is an error."""
        session, _ = self.parent()
        error_of(self.subagent, {"task": "   "}, self.cwd, session=session)
