"""Step 5: the provider.

Converts Pi's messages and tools to the OpenAI chat format, sends the request, and turns the streamed
answer back into Pi events: thinking, text and tool calls. Works with any OpenAI-compatible endpoint,
such as Ollama's http://localhost:11434/v1. Like pi-ai, nothing above this file knows the wire format.
"""

import json
import urllib.error
import urllib.request

from . import __version__
from .compaction import SUMMARY_PREFIX, SUMMARY_SUFFIX

# Message shapes used everywhere in pi2 (the same roles as Pi):
#   {"role": "user", "content": "text"}
#   {"role": "assistant", "content": [blocks], "stop_reason": ..., "usage": {"input": n, "output": n}}
#       blocks: {"type": "thinking", "text"}, {"type": "text", "text"},
#               {"type": "toolCall", "id", "name", "arguments": {...}}
#   {"role": "toolResult", "tool_call_id", "tool_name", "content": "text", "is_error": bool}
#   {"role": "compaction", "summary": "text", "tokens_before": n}  (sent as a user message)


def stream(model, context, api_key):
    """Stream one assistant answer. Yields delta events, then {"type": "done", "message": ...}."""
    body = {
        "model": model["id"],
        "messages": convert_messages(context["system_prompt"], context["messages"]),
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if context["tools"]:
        body["tools"] = convert_tools(context["tools"])
    if model.get("max_tokens"):
        body["max_tokens"] = model["max_tokens"]

    request = urllib.request.Request(
        f"{model['base_url'].rstrip('/')}/chat/completions",
        data=json.dumps(body).encode(),
        # Like Pi, name the client: some servers behind Cloudflare refuse Python's default User-Agent.
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": f"pi2/{__version__}",
        },
    )
    message = {"role": "assistant", "content": [], "stop_reason": "stop", "usage": {"input": 0, "output": 0}}
    calls = {}  # the provider streams each tool call in pieces, keyed by its index

    try:
        response = urllib.request.urlopen(request, timeout=600)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"{error.code} {error.read().decode(errors='replace')}") from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"Cannot reach {model['base_url']}: {error.reason}") from None

    with response:
        for raw in response:  # server-sent events: one "data: {json}" line per chunk
            line = raw.decode().strip()
            if not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if chunk.get("usage"):
                message["usage"] = {
                    "input": chunk["usage"].get("prompt_tokens", 0),
                    "output": chunk["usage"].get("completion_tokens", 0),
                }
            for choice in chunk.get("choices", []):
                delta = choice.get("delta") or {}
                thinking = delta.get("reasoning_content") or delta.get("reasoning")
                if thinking:
                    append_text(message, "thinking", thinking)
                    yield {"type": "thinking_delta", "delta": thinking}
                if delta.get("content"):
                    append_text(message, "text", delta["content"])
                    yield {"type": "text_delta", "delta": delta["content"]}
                for call in delta.get("tool_calls") or []:
                    index = call.get("index", len(calls))
                    if index not in calls:
                        calls[index] = {"type": "toolCall", "id": call.get("id") or f"call_{index}", "name": "", "json": ""}
                        message["content"].append(calls[index])
                    function = call.get("function") or {}
                    calls[index]["name"] += function.get("name") or ""
                    calls[index]["json"] += function.get("arguments") or ""
                if choice.get("finish_reason") == "length":
                    message["stop_reason"] = "length"

    for call in calls.values():
        call["arguments"] = parse_arguments(call.pop("json"))
    if calls and message["stop_reason"] != "length":
        message["stop_reason"] = "tool_use"
    yield {"type": "done", "message": message}


def append_text(message, block_type, delta):
    """Add a delta to the last block if it has the same type, else start a new block."""
    content = message["content"]
    if content and content[-1]["type"] == block_type:
        content[-1]["text"] += delta
    else:
        content.append({"type": block_type, "text": delta})


def parse_arguments(text):
    """Tool arguments arrive as a JSON string. Invalid JSON becomes {} and fails validation later."""
    try:
        value = json.loads(text or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def convert_messages(system_prompt, messages):
    """Pi's messages to OpenAI chat messages. Thinking is not sent back."""
    result = [{"role": "system", "content": system_prompt}]
    for message in messages:
        if message["role"] == "user":
            result.append({"role": "user", "content": message["content"]})
        elif message["role"] == "compaction":  # the summary of older messages, see compaction.py
            result.append({"role": "user", "content": SUMMARY_PREFIX + message["summary"] + SUMMARY_SUFFIX})
        elif message["role"] == "assistant":
            text = "".join(block["text"] for block in message["content"] if block["type"] == "text")
            entry = {"role": "assistant", "content": text}
            calls = [block for block in message["content"] if block["type"] == "toolCall"]
            if calls:
                entry["tool_calls"] = [
                    {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
                    for c in calls
                ]
            result.append(entry)
        elif message["role"] == "toolResult":
            result.append({"role": "tool", "tool_call_id": message["tool_call_id"], "content": message["content"]})
    return result


def convert_tools(tools):
    """Pi's tool definitions to OpenAI function declarations: name, description, JSON Schema."""
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
        for t in tools
    ]
