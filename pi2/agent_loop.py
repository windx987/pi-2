"""Steps 3, 6, 7 and 8: the agent loop.

Asks the model for an answer, runs the tool calls in it, adds the results, and asks again. Stops when an
answer has no tool calls. Like Pi's packages/agent, it knows no provider and no terminal: it calls
`config["stream_fn"]` for the model and reports what happens through `emit(event)`.
"""

from .schema import validate_tool_arguments


def run(context, config, emit):
    """Run the loop on context = {"system_prompt", "messages", "tools"} until the model stops calling tools."""
    emit({"type": "agent_start"})
    while True:
        # Step 3 -> 4 -> 5: one model request, streamed.
        message = stream_assistant_response(context, config, emit)
        tool_calls = [block for block in message["content"] if block["type"] == "toolCall"]
        if message["stop_reason"] in ("error", "aborted") or not tool_calls:
            emit({"type": "agent_end"})
            return

        for call in tool_calls:
            result = execute_tool_call(context, call, config, emit)
            # Step 8: the result joins the conversation, so the model sees it on the next turn.
            context["messages"].append(result)
            emit({"type": "message_end", "message": result})
            if result.get("aborted"):
                emit({"type": "agent_end"})
                return


def stream_assistant_response(context, config, emit):
    """Stream one answer from the model, emitting each delta. Errors and ctrl+c end the answer early."""
    emit({"type": "message_start", "role": "assistant"})
    partial = {"role": "assistant", "content": [], "stop_reason": "stop", "usage": {"input": 0, "output": 0}}
    try:
        for event in config["stream_fn"](config["model"], context):
            if event["type"] == "done":
                message = event["message"]
                break
            emit({"type": "message_update", "event": event})
            kind = "thinking" if event["type"] == "thinking_delta" else "text"
            if partial["content"] and partial["content"][-1]["type"] == kind:
                partial["content"][-1]["text"] += event["delta"]
            else:
                partial["content"].append({"type": kind, "text": event["delta"]})
        else:
            raise RuntimeError("The provider ended the stream without an answer.")
    except KeyboardInterrupt:
        message = {**partial, "stop_reason": "aborted"}
    except Exception as error:  # the provider failed: report it as the answer, as Pi does
        message = {**partial, "stop_reason": "error", "error_message": str(error)}
    if message["stop_reason"] == "length":
        # The answer was cut off, so its tool calls may carry truncated arguments: do not run them.
        message["content"] = [block for block in message["content"] if block["type"] != "toolCall"]
    context["messages"].append(message)
    emit({"type": "message_end", "message": message})
    return message


def execute_tool_call(context, call, config, emit):
    """Steps 6 and 7: validate the arguments, let extensions block the call, run the tool."""
    emit({"type": "tool_execution_start", "tool_call": call})
    result = {"role": "toolResult", "tool_call_id": call["id"], "tool_name": call["name"], "is_error": False}
    try:
        tool = next((t for t in context["tools"] if t.name == call["name"]), None)
        if tool is None:
            raise ValueError(f"Tool {call['name']} not found")
        # Step 6: the model's arguments must match the tool's JSON Schema.
        args = validate_tool_arguments(tool, call["arguments"])
        blocked = config["before_tool_call"](call, args)
        if blocked:
            raise ValueError(blocked)
        # Step 7: the tool runs. In pi/2 every tool comes from an extension (-e).
        result["content"] = str(tool.execute(args, config["tool_context"]))
    except KeyboardInterrupt:
        result.update(content="Operation aborted", is_error=True, aborted=True)
    except Exception as error:  # a raised error becomes an error result the model reads
        result.update(content=str(error) or type(error).__name__, is_error=True)
    emit({"type": "tool_execution_end", "tool_call": call, "result": result})
    return result
