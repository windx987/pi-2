"""Compaction: keeps the conversation inside the model's context window.

Every request sends the whole conversation, so it grows with each tool result. When it nears the
window, the session asks the model to summarize the older messages and keeps only the summary and the
newest messages. Follows Pi's packages/coding-agent/src/core/compaction/, without split turns or
branches. The session file keeps every message; only what the model sees gets shorter.
"""

import json
import re
from pathlib import Path

# Pi's defaults. A small window gets less: half of it for the answer, an eighth kept word for word, so
# that a compacted conversation is well below the threshold and /compact frees room well before it.
RESERVE_TOKENS = 16384
KEEP_RECENT_TOKENS = 20000
TOOL_RESULT_MAX_CHARS = 2000

# Error texts of providers whose request did not fit: OpenAI, vLLM, llama.cpp, Anthropic and others.
OVERFLOW = re.compile(
    r"context.?length|context.?window|maximum context|max_model_len|maximum model length|too many tokens"
    r"|prompt is too long|input is too long|exceeds the context",
    re.IGNORECASE,
)

SUMMARY_PREFIX = "The conversation history before this point was compacted into the following summary:\n\n<summary>\n"
SUMMARY_SUFFIX = "\n</summary>"

SYSTEM_PROMPT = (
    "You are a context summarization assistant. Your task is to read a conversation between a user and an "
    "AI assistant, then produce a structured summary following the exact format specified.\n\n"
    "Do NOT continue the conversation. Do NOT respond to any questions in the conversation. "
    "ONLY output the structured summary."
)

FORMAT = """## Goal
[What is the user trying to accomplish?]

## Constraints & Preferences
- [Constraints, preferences or requirements the user mentioned, or "(none)"]

## Progress
### Done
- [x] [Completed tasks and changes]

### In Progress
- [ ] [Current work]

## Key Decisions
- **[Decision]**: [Brief rationale]

## Next Steps
1. [What should happen next, in order]

## Critical Context
- [Data, examples or references needed to continue, or "(none)"]

Keep each section concise. Preserve exact file paths, function names, and error messages."""

PROMPT = (
    "The messages above are a conversation to summarize. Create a structured context checkpoint summary "
    "that another LLM will use to continue the work.\n\nUse this EXACT format:\n\n" + FORMAT
)

UPDATE_PROMPT = (
    "The messages above are NEW conversation messages to incorporate into the existing summary provided in "
    "<previous-summary> tags. Keep everything in the previous summary that still matters, add the new "
    "progress, decisions and context, and move finished items to Done.\n\nUse this EXACT format:\n\n" + FORMAT
)


def load_settings(agent_dir, context_window):
    """The "compaction" settings from settings.json, as in Pi, with defaults that fit the window."""
    settings = {
        "enabled": True,
        "reserve_tokens": min(RESERVE_TOKENS, context_window // 2),
        "keep_recent_tokens": min(KEEP_RECENT_TOKENS, context_window // 8),
    }
    path = Path(agent_dir) / "settings.json"
    if path.exists():
        saved = json.loads(path.read_text()).get("compaction", {})
        settings["enabled"] = saved.get("enabled", settings["enabled"])
        settings["reserve_tokens"] = saved.get("reserveTokens", settings["reserve_tokens"])
        settings["keep_recent_tokens"] = saved.get("keepRecentTokens", settings["keep_recent_tokens"])
    return settings


def should_compact(context_tokens, context_window, settings):
    """Pi's rule: compact when the context leaves less than reserve_tokens for the answer."""
    return settings["enabled"] and context_tokens > context_window - settings["reserve_tokens"]


def is_context_overflow(message):
    """Whether the provider rejected the request because it did not fit the window."""
    return message.get("stop_reason") == "error" and bool(OVERFLOW.search(message.get("error_message", "")))


def estimate_tokens(message):
    """About four characters per token, as Pi estimates. Real counts come only with the model's answer."""
    if message["role"] == "compaction":
        chars = len(message["summary"])
    elif message["role"] == "assistant":
        chars = sum(len(block.get("text", "")) + len(json.dumps(block.get("arguments", "")))
                    for block in message["content"])
    else:
        chars = len(message["content"])
    return chars // 4 + 1


def find_cut(messages, keep_recent_tokens):
    """The index of the first message to keep: about keep_recent_tokens from the end.

    Never cuts at a tool result, which must stay with the tool call it answers: the cut moves back to the
    call. Returns 0, or 1 after an earlier summary, when there is nothing to summarize.
    """
    start = 1 if messages and messages[0]["role"] == "compaction" else 0
    kept = 0
    for index in range(len(messages) - 1, start - 1, -1):
        kept += estimate_tokens(messages[index])
        if kept >= keep_recent_tokens:
            while index > start and messages[index]["role"] == "toolResult":
                index -= 1
            return index
    return start


def serialize(messages):
    """The conversation as plain text, so the model summarizes it instead of continuing it."""
    parts = []
    for message in messages:
        if message["role"] == "user":
            parts.append(f"[User]: {message['content']}")
        elif message["role"] == "assistant":
            text = "".join(block["text"] for block in message["content"] if block["type"] == "text")
            calls = [f"{block['name']}({', '.join(f'{k}={json.dumps(v)}' for k, v in block['arguments'].items())})"
                     for block in message["content"] if block["type"] == "toolCall"]
            if text:
                parts.append(f"[Assistant]: {text}")
            if calls:
                parts.append(f"[Assistant tool calls]: {'; '.join(calls)}")
        elif message["role"] == "toolResult":
            content = message["content"]
            if len(content) > TOOL_RESULT_MAX_CHARS:
                content = content[:TOOL_RESULT_MAX_CHARS] + f"\n[... {len(content) - TOOL_RESULT_MAX_CHARS} more characters]"
            parts.append(f"[Tool result]: {content}")
    return "\n\n".join(parts)


def file_lists(messages):
    """Files the summarized messages read and changed, appended to the summary as Pi does."""
    read, modified = [], []
    for message in messages:
        for block in message["content"] if message["role"] == "assistant" else []:
            path = block.get("arguments", {}).get("path") if block["type"] == "toolCall" else None
            if not isinstance(path, str):
                continue
            target = read if block["name"] == "read" else modified if block["name"] in ("write", "edit") else None
            if target is not None and path not in target:
                target.append(path)
    text = ""
    if read:
        text += "\n\n<read-files>\n" + "\n".join(read) + "\n</read-files>"
    if modified:
        text += "\n\n<modified-files>\n" + "\n".join(modified) + "\n</modified-files>"
    return text


def summarize(messages, previous_summary, instructions, model, stream_fn):
    """Ask the model for a summary of messages, updating previous_summary if there is one."""
    text = f"<conversation>\n{serialize(messages)}\n</conversation>\n\n"
    if previous_summary:
        text += f"<previous-summary>\n{previous_summary}\n</previous-summary>\n\n"
    text += UPDATE_PROMPT if previous_summary else PROMPT
    if instructions:
        text += f"\n\nAdditional focus: {instructions}"
    context = {"system_prompt": SYSTEM_PROMPT, "messages": [{"role": "user", "content": text}], "tools": []}
    answer = None
    try:
        for event in stream_fn(model, context):
            if event["type"] == "done":
                answer = event["message"]
    except RuntimeError as error:  # the provider failed, as in agent_loop
        raise RuntimeError(f"Summarization failed: {error}") from None
    if answer is None or answer["stop_reason"] == "error":
        raise RuntimeError(f"Summarization failed: {(answer or {}).get('error_message', 'no answer')}")
    if answer["stop_reason"] == "length":
        raise RuntimeError("Summarization failed: the answer hit the token limit and the summary is incomplete")
    summary = "".join(block["text"] for block in answer["content"] if block["type"] == "text").strip()
    if not summary:
        raise RuntimeError("Summarization failed: the model returned no text")
    return summary
