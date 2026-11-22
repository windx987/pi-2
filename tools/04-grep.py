import fnmatch
import re
from pi2 import ExtensionAPI, define_tool


def execute(params, ctx):
    # TODO: resolve and validate the search directory
    # TODO: compile the regex and walk matching files
    # TODO: return relative path, line, and text
    raise NotImplementedError


grep_tool = define_tool(
    name="grep",
    label="grep",
    description="Search UTF-8 file contents recursively with a regular expression.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string"},
            "path": {"type": "string"},
            "include": {"type": "string"},
        },
        "required": ["pattern"],
    },
    execute=execute,
)


def extension(pi: ExtensionAPI):
    pi.register_tool(grep_tool)
