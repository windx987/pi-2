"""Tests for pi2, without a real model: a fake stream function for the loop, a local HTTP server for the
provider. Run from the repository root:  python3 -m unittest discover tests
"""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from pi2 import ExtensionAPI, define_tool
from pi2 import agent_loop, ai, compaction, tui
from pi2.extensions import ToolContext
from pi2.model_runtime import ModelRuntime
from pi2.session import AgentSession

ECHO = define_tool(
    name="echo",
    label="echo",
    description="Echo text",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    execute=lambda params, ctx: f"echo: {params['text']}",
)


def answer(*blocks, stop_reason="stop"):
    return {"role": "assistant", "content": list(blocks), "stop_reason": stop_reason, "usage": {"input": 10, "output": 5}}


def call(name, arguments, id="call_1"):
    return {"type": "toolCall", "id": id, "name": name, "arguments": arguments}


def fake_stream(*answers):
    """A stream function that replays prepared answers and records the contexts it was called with."""
    queue, seen = list(answers), []

    def stream_fn(model, context):
        seen.append([dict(m) for m in context["messages"]])
        message = queue.pop(0)
        for block in message["content"]:
            if block["type"] == "text":
                yield {"type": "text_delta", "delta": block["text"]}
        yield {"type": "done", "message": message}

    return stream_fn, seen


def run_loop(stream_fn, tools=(ECHO,), before=lambda call, args: None):
    context = {"system_prompt": "test", "messages": [{"role": "user", "content": "hi"}], "tools": list(tools)}
    events = []
    config = {"model": {}, "stream_fn": stream_fn, "before_tool_call": before, "tool_context": ToolContext(cwd="/tmp")}
    agent_loop.run(context, config, events.append)
    return context["messages"], events


class AgentLoopTest(unittest.TestCase):
    def test_answer_without_tool_calls_ends_the_loop(self):
        messages, events = run_loop(fake_stream(answer({"type": "text", "text": "hello"}))[0])
        self.assertEqual([m["role"] for m in messages], ["user", "assistant"])
        self.assertEqual(events[-1]["type"], "agent_end")

    def test_tool_call_runs_and_its_result_reaches_the_next_request(self):
        stream_fn, seen = fake_stream(
            answer(call("echo", {"text": "x"}), stop_reason="tool_use"), answer({"type": "text", "text": "done"})
        )
        messages, _ = run_loop(stream_fn)
        self.assertEqual([m["role"] for m in messages], ["user", "assistant", "toolResult", "assistant"])
        self.assertEqual(messages[2]["content"], "echo: x")
        self.assertEqual(seen[1][-1]["role"], "toolResult")

    def test_invalid_arguments_become_an_error_result(self):
        stream_fn, _ = fake_stream(answer(call("echo", {"text": 3})), answer({"type": "text", "text": "ok"}))
        messages, _ = run_loop(stream_fn)
        self.assertTrue(messages[2]["is_error"])
        self.assertIn("text: must be string", messages[2]["content"])

    def test_unknown_tool_and_raised_errors_become_error_results(self):
        failing = define_tool(name="fail", label="fail", description="", parameters={"type": "object"},
                              execute=lambda params, ctx: 1 / 0)
        stream_fn, _ = fake_stream(
            answer(call("missing", {}, "a"), call("fail", {}, "b")), answer({"type": "text", "text": "ok"})
        )
        messages, _ = run_loop(stream_fn, tools=[failing])
        self.assertEqual(messages[2]["content"], "Tool missing not found")
        self.assertEqual(messages[3]["content"], "division by zero")

    def test_an_extension_can_block_a_call(self):
        stream_fn, _ = fake_stream(answer(call("echo", {"text": "x"})), answer({"type": "text", "text": "ok"}))
        messages, _ = run_loop(stream_fn, before=lambda call, args: "not allowed")
        self.assertEqual(messages[2]["content"], "not allowed")

    def test_cut_off_answer_runs_no_tools(self):
        stream_fn, _ = fake_stream(answer(call("echo", {"text": "x"}), stop_reason="length"))
        messages, _ = run_loop(stream_fn)
        self.assertEqual([m["role"] for m in messages], ["user", "assistant"])

    def test_provider_error_ends_the_loop_with_an_error_message(self):
        def broken(model, context):
            raise RuntimeError("401 unauthorized")
            yield

        messages, _ = run_loop(broken)
        self.assertEqual(messages[-1]["stop_reason"], "error")
        self.assertEqual(messages[-1]["error_message"], "401 unauthorized")


class SessionTest(unittest.TestCase):
    def test_extension_tools_are_offered_and_messages_are_saved(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            extensions = ExtensionAPI()
            extensions.register_tool(ECHO)
            stream_fn, _ = fake_stream(answer(call("echo", {"text": "x"})), answer({"type": "text", "text": "ok"}))
            runtime = ModelRuntime(agent_dir)
            runtime.stream_fn = stream_fn
            session = AgentSession(runtime, {"id": "fake"}, extensions, "/work", agent_dir)
            session.prompt("hi")
            lines = [json.loads(line) for line in session.session_file.read_text().splitlines()]
            self.assertEqual(lines[0]["type"], "session")
            self.assertEqual([line["message"]["role"] for line in lines[1:]], ["user", "assistant", "toolResult", "assistant"])
            self.assertIn("- echo: Echo text", session.system_prompt(list(extensions.tools.values())))

    def test_tools_get_the_running_session(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            seen = []
            extensions = ExtensionAPI()
            extensions.register_tool(define_tool(name="peek", label="peek", description="", parameters={"type": "object"},
                                                 execute=lambda params, ctx: seen.append(ctx) or "ok"))
            stream_fn, _ = fake_stream(answer(call("peek", {})), answer({"type": "text", "text": "ok"}))
            runtime = ModelRuntime(agent_dir)
            runtime.stream_fn = stream_fn
            session = AgentSession(runtime, {"id": "fake"}, extensions, "/work", agent_dir)
            session.prompt("hi")
            self.assertIs(seen[0].session, session)
            self.assertEqual(seen[0].cwd, "/work")

    def test_extension_files_are_loaded(self):
        extensions = ExtensionAPI()
        extensions.load(Path(__file__).parent.parent / "examples" / "hello.py")
        self.assertEqual(extensions.tools["hello"].execute({"name": "Ada"}, None), "Hello, Ada!")


def session_with(stream_fn, agent_dir, keep_recent_tokens=1, reserve_tokens=16384):
    extensions = ExtensionAPI()
    extensions.register_tool(ECHO)
    runtime = ModelRuntime(agent_dir)
    runtime.stream_fn = stream_fn
    session = AgentSession(runtime, {"id": "fake", "context_window": 32768}, extensions, "/work", agent_dir)
    session.compaction_settings.update(keep_recent_tokens=keep_recent_tokens, reserve_tokens=reserve_tokens)
    return session


class CompactionTest(unittest.TestCase):
    def test_the_cut_keeps_recent_messages_and_never_splits_a_tool_call_from_its_result(self):
        messages = [{"role": "user", "content": "a" * 400}, answer(call("echo", {"text": "x"})),
                    {"role": "toolResult", "tool_call_id": "call_1", "tool_name": "echo", "content": "b" * 400}]
        self.assertEqual(compaction.find_cut(messages, 50), 1)  # at the call, not at its result
        self.assertEqual(compaction.find_cut(messages, 10_000), 0)  # all fits: nothing to summarize

    def test_defaults_shrink_for_a_small_window_and_settings_json_overrides_them(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            settings = compaction.load_settings(agent_dir, 32768)
            self.assertEqual((settings["reserve_tokens"], settings["keep_recent_tokens"]), (16384, 8192))
            Path(agent_dir, "settings.json").write_text(json.dumps({"compaction": {"keepRecentTokens": 500}}))
            self.assertEqual(compaction.load_settings(agent_dir, 32768)["keep_recent_tokens"], 500)

    def test_compact_replaces_old_messages_with_a_summary_the_model_sees_next(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            stream_fn, seen = fake_stream(answer({"type": "text", "text": "first answer"}),
                                          answer({"type": "text", "text": "## Goal\nsay hi"}),
                                          answer({"type": "text", "text": "second answer"}))
            session = session_with(stream_fn, agent_dir)
            session.prompt("hi")
            session.compact("keep the greeting")
            self.assertEqual([m["role"] for m in session.messages], ["compaction", "assistant"])
            request = seen[1][0]["content"]
            self.assertIn("[User]: hi", request)
            self.assertIn("Additional focus: keep the greeting", request)
            session.prompt("again")
            sent = ai.convert_messages("sys", seen[2])
            self.assertIn("<summary>\n## Goal\nsay hi", sent[1]["content"])
            self.assertEqual(sent[1]["role"], "user")

    def test_context_tokens_count_system_prompt_and_tools_until_the_model_counts(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            stream_fn, _ = fake_stream(answer({"type": "text", "text": "ok"}))
            session = session_with(stream_fn, agent_dir)
            self.assertGreater(session.context_tokens(), 50)  # the system prompt and the echo tool
            session.prompt("hi")
            self.assertEqual(session.context_tokens(), 15)  # the model's count: 10 in, 5 out

    def test_context_command_shows_the_parts_and_the_threshold(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            stream_fn, _ = fake_stream(answer(call("echo", {"text": "x"})), answer({"type": "text", "text": "ok"}))
            session = session_with(stream_fn, agent_dir)
            session.prompt("hi")
            parts = {label: count for label, _, count in session.context_parts()}
            self.assertEqual(parts, {"system prompt": 1, "tools": 1, "summary": 0, "your messages": 1,
                                     "answers": 2, "tool results": 1})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                tui.InteractiveMode(session).command("/context")
            self.assertIn("compacts above 16k", out.getvalue())
            self.assertIn("(2 messages)", out.getvalue())
            self.assertNotIn("summary", out.getvalue())  # parts with nothing in them are left out

    def test_a_full_context_is_compacted_between_turns(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            full = answer(call("echo", {"text": "x"}), stop_reason="tool_use")
            full["usage"] = {"input": 20000, "output": 100}  # over 32768 - 16384
            stream_fn, seen = fake_stream(full, answer({"type": "text", "text": "summary"}),
                                          answer({"type": "text", "text": "done"}))
            session = session_with(stream_fn, agent_dir)
            session.prompt("hi")
            self.assertIn("<conversation>", seen[1][0]["content"])  # the summary request
            self.assertEqual([m["role"] for m in seen[2]], ["compaction", "assistant", "toolResult"])
            self.assertEqual(session.messages[-1]["content"][0]["text"], "done")

    def test_the_models_count_scales_the_estimates(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            stream_fn, _ = fake_stream(answer({"type": "text", "text": "ok"}), answer({"type": "text", "text": "ok"}))
            session = session_with(stream_fn, agent_dir)
            system, schemas, _ = session.fixed_parts()
            dense = answer({"type": "text", "text": "ok"})
            dense["usage"] = {"input": 2 * (system + schemas + 2), "output": 5}  # twice the estimate, like logs
            stream_fn, _ = fake_stream(dense)
            session.runtime.stream_fn = stream_fn
            session.prompt("hi")
            self.assertAlmostEqual(session.ratio, 2.0, delta=0.1)
            later = {"role": "user", "content": "x" * 400}
            self.assertAlmostEqual(session.estimate([later]), 202, delta=10)  # 101 estimated, times 2

    def test_compaction_keeps_model_tokens_so_it_does_not_compact_again_at_once(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            stream_fn, _ = fake_stream(answer({"type": "text", "text": "## Goal\nread the logs"}))
            session = session_with(stream_fn, agent_dir, keep_recent_tokens=400)
            session.messages = [{"role": "user", "content": "read the logs"}]
            for i in range(6):  # six tool results of 100 estimated tokens each
                session.messages += [answer(call("echo", {"text": str(i)}, id=f"call_{i}"), stop_reason="tool_use"),
                                     {"role": "toolResult", "tool_call_id": f"call_{i}", "tool_name": "echo",
                                      "content": "log " * 100}]
            session.ratio = 2.0  # the model counted twice as many tokens as four characters each
            session.compact()
            results = [m for m in session.messages if m["role"] == "toolResult"]
            self.assertEqual(len(results), 2)  # 400 model tokens: two results, not the four 400 estimated ones are

    def test_an_overflow_error_compacts_and_retries_once(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            overflow = answer(stop_reason="error")
            overflow["error_message"] = "400 This model's maximum context length is 32768 tokens."
            stream_fn, seen = fake_stream(answer({"type": "text", "text": "ok"}), overflow,
                                          answer({"type": "text", "text": "summary"}),
                                          answer({"type": "text", "text": "retried"}))
            session = session_with(stream_fn, agent_dir)
            session.prompt("hi")
            session.prompt("go on")
            self.assertEqual([m["role"] for m in seen[3]], ["compaction", "user"])
            self.assertEqual(session.messages[-1]["content"][0]["text"], "retried")


class ModelRuntimeTest(unittest.TestCase):
    def test_models_are_found_by_number_id_or_provider_and_id(self):
        with tempfile.TemporaryDirectory() as agent_dir:
            models = [{"id": "a"}, {"id": "b", "contextWindow": 8000}]
            config = {"providers": {"ollama": {"baseUrl": "http://localhost:11434/v1", "models": models}}}
            Path(agent_dir, "models.json").write_text(json.dumps(config))
            runtime = ModelRuntime(agent_dir)
            self.assertEqual(runtime.find()["id"], "a")
            self.assertEqual(runtime.match("2")["id"], "b")
            self.assertEqual(runtime.match("b")["context_window"], 8000)
            self.assertEqual(runtime.match("ollama/a")["id"], "a")
            self.assertIsNone(runtime.match("3"))
            self.assertIsNone(runtime.match("other/a"))


class ProviderTest(unittest.TestCase):
    def test_streamed_text_thinking_and_tool_call_arguments_are_assembled(self):
        chunks = [
            {"choices": [{"delta": {"reasoning_content": "Let me "}}]},
            {"choices": [{"delta": {"reasoning_content": "look."}}]},
            {"choices": [{"delta": {"content": "Reading."}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "c1", "function": {"name": "echo", "arguments": '{"te'}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": 'xt": "x"}'}}]}, "finish_reason": "tool_calls"}]},
            {"choices": [], "usage": {"prompt_tokens": 12, "completion_tokens": 7}},
        ]
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for chunk in chunks:
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
                self.wfile.write(b"data: [DONE]\n\n")

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            model = {"id": "m", "base_url": f"http://127.0.0.1:{server.server_port}/v1"}
            context = {"system_prompt": "sys", "messages": [{"role": "user", "content": "hi"}], "tools": [ECHO]}
            events = list(ai.stream(model, context, "key"))
        finally:
            server.shutdown()
            server.server_close()

        message = events[-1]["message"]
        self.assertEqual([e["type"] for e in events[:3]], ["thinking_delta", "thinking_delta", "text_delta"])
        self.assertEqual(message["content"][0], {"type": "thinking", "text": "Let me look."})
        self.assertEqual(message["content"][2]["arguments"], {"text": "x"})
        self.assertEqual(message["stop_reason"], "tool_use")
        self.assertEqual(message["usage"], {"input": 12, "output": 7})
        self.assertEqual(requests[0]["messages"][0], {"role": "system", "content": "sys"})
        self.assertEqual(requests[0]["tools"][0]["function"]["name"], "echo")


class InteractiveModeTest(unittest.TestCase):
    def render_end(self, message):
        class Session:
            def subscribe(self, listener):
                pass

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            tui.InteractiveMode(Session()).on_event({"type": "message_end", "message": message})
        return out.getvalue()

    def test_an_empty_answer_says_so(self):
        self.assertIn("without a reply", self.render_end(answer()))
        self.assertIn("without a reply", self.render_end(answer({"type": "thinking", "text": "hmm"}, {"type": "text", "text": " \n"})))

    def test_answers_with_text_or_tool_calls_get_no_note(self):
        self.assertNotIn("without a reply", self.render_end(answer({"type": "text", "text": "hello"})))
        self.assertNotIn("without a reply", self.render_end(answer(call("echo", {"text": "x"}), stop_reason="tool_use")))

    def test_a_truncated_answer_says_so(self):
        self.assertIn("truncated", self.render_end(answer({"type": "text", "text": "cut"}, stop_reason="length")))



class ExerciseChecksTest(unittest.TestCase):
    def test_every_check_is_todo_on_the_starters(self):
        """exercises/check.py runs, and shows TODO, not FAIL, while execute() raises NotImplementedError."""
        script = Path(__file__).parent.parent / "exercises" / "check.py"
        run = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=120)
        self.assertNotIn("FAIL", run.stdout, run.stdout + run.stderr)
        self.assertRegex(run.stdout, r"\n0 of (44|47) checks pass\.", run.stdout + run.stderr)  # 47 with Docker running

if __name__ == "__main__":
    unittest.main()
