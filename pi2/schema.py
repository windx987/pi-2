"""Step 6: checks the model's tool arguments against the tool's JSON Schema.

Pi does this with pi-schema (`validateToolArguments` in Pi's packages/ai). This version covers the parts of
JSON Schema the tools use: object, properties, required, string, number, integer, boolean, array, items.
"""

import json

TYPES = {
    "string": lambda v: isinstance(v, str),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
}


def validate_tool_arguments(tool, args):
    """Return the arguments if they match the schema; raise ValueError with every problem otherwise."""
    problems = []
    check(tool.parameters, args, "", problems)
    if problems:
        lines = "\n".join(f"  - {path or 'root'}: {problem}" for path, problem in problems)
        raise ValueError(
            f'Validation failed for tool "{tool.name}":\n{lines}\n\nReceived arguments:\n{json.dumps(args, indent=2)}'
        )
    return args


def check(schema, value, path, problems):
    expected = schema.get("type")
    if expected and not TYPES[expected](value):
        problems.append((path, f"must be {expected}"))
        return
    if expected == "object":
        for name in schema.get("required", []):
            if name not in value:
                problems.append((join(path, name), "is required"))
        for name, child in schema.get("properties", {}).items():
            if name in value:
                check(child, value[name], join(path, name), problems)
    elif expected == "array" and "items" in schema:
        for index, item in enumerate(value):
            check(schema["items"], item, f"{path}[{index}]", problems)
    if "enum" in schema and value not in schema["enum"]:
        problems.append((path, f"must be one of {schema['enum']}"))


def join(path, name):
    return f"{path}.{name}" if path else name
