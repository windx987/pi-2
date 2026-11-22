# Checks the exercise tools without a model: each test file calls execute() the way pi2 would.
#
# From the repository root:
#   python3 exercises/check.py                    # every exercise
#   python3 exercises/check.py 03                 # one exercise
#   python3 exercises/check.py 06 tools/06-subagent.py   # check a specific tool file
#
# The checks for an exercise live in test_<tool>.py next to its starter.

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # the repository root, where the pi2 package is

from pi2 import ExtensionAPI, ToolContext  # noqa: E402

GREEN, RED, YELLOW, DIM, RESET = "\x1b[32m", "\x1b[31m", "\x1b[33m", "\x1b[2m", "\x1b[0m"

# The tool each exercise builds and its numbered reference filename.
TOOLS = {
    "01": ("read", "01-read"),
    "02": ("write", "02-write"),
    "03": ("edit", "03-edit"),
    "04": ("grep", "04-grep"),
    "05": ("bash", "05-bash"),
    "06": ("subagent", "06-subagent"),
}

unittest.TestCase.longMessage = False  # a check's own message says what is wrong


class NotDone(unittest.SkipTest):
    """The tool still raises NotImplementedError: shown as TODO, not as a failure."""


def load_tool(name):
    """The tool `name` from the file being checked."""
    path = os.environ["PI2_CHECK_FILE"]
    api = ExtensionAPI()
    api.load(path)
    if name not in api.tools:
        raise AssertionError(f"{path} registers no tool named {name}.")
    return api.tools[name]


def call(tool, params, cwd, session=None):
    """Run the tool's execute() and return its result as text."""
    try:
        result = tool.execute(params, ToolContext(cwd=str(cwd), session=session))
    except NotImplementedError as error:
        raise NotDone(str(error)) from None
    except Exception as error:  # noqa: BLE001  (the check failed: show what the tool said)
        raise AssertionError(f"{params} raised {type(error).__name__}: {error}") from None
    if not isinstance(result, str):
        raise AssertionError(f"execute() returned {type(result).__name__}, not text (str): {result!r}")
    return result


def error_of(tool, params, cwd, session=None):
    """Run the tool's execute(), which must raise. Returns the exception."""
    try:
        result = tool.execute(params, ToolContext(cwd=str(cwd), session=session))
    except NotImplementedError as error:
        raise NotDone(str(error)) from None
    except Exception as error:  # noqa: BLE001  (expected: pi2 turns it into an error result)
        return error
    raise AssertionError(f"{params} should raise an exception (an error result), but returned {result!r}")


class Workspace(unittest.TestCase):
    """A test case with an empty working directory in self.cwd, and the process somewhere else."""

    def setUp(self):
        # Under the home directory, like the playground copy; macOS /tmp is a symlink that hides bugs.
        self.cwd = Path(tempfile.mkdtemp(dir=Path.home(), prefix="pi2-check-")).resolve()
        self.addCleanup(shutil.rmtree, self.cwd, ignore_errors=True)
        previous = os.getcwd()
        os.chdir(tempfile.gettempdir())  # a relative path must not work by accident
        self.addCleanup(os.chdir, previous)


class Result(unittest.TestResult):
    """Prints one line per check: PASS, FAIL with the reason, or TODO."""

    def __init__(self):
        super().__init__()
        self.passed = 0

    def addSuccess(self, test):
        self.passed += 1
        print(f"  {GREEN}PASS{RESET}  {describe(test)}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        print(f"  {RED}FAIL{RESET}  {describe(test)}")
        print("".join(f"        {DIM}{line}{RESET}\n" for line in str(err[1]).splitlines()[:6]), end="")

    def addError(self, test, err):
        super().addError(test, err)
        print(f"  {RED}FAIL{RESET}  {describe(test)}")
        print(f"        {DIM}{err[0].__name__}: {err[1]}{RESET}")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        print(f"  {YELLOW}TODO{RESET}  {describe(test)} {DIM}(not implemented yet){RESET}")


def describe(test):
    return (test.shortDescription() or test.id().rsplit(".", 1)[-1]).rstrip(".")


def check(folder, path):
    """Run test_*.py of one exercise folder against the tool file at path. Returns (passed, total)."""
    os.environ["PI2_CHECK_FILE"] = str(path)
    suite = unittest.TestSuite()
    print(f"\n{folder.name}  {DIM}{path}{RESET}")
    for test_file in sorted(folder.glob("test_*.py")):
        spec = importlib.util.spec_from_file_location(f"{folder.name}.{test_file.stem}", test_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = Result()
    suite.run(result)
    return result.passed, result.testsRun


def main():
    sys.modules["check"] = sys.modules[__name__]  # the test files import this module as `check`
    args = sys.argv[1:]
    folders = sorted(p for p in HERE.iterdir() if p.is_dir() and list(p.glob("test_*.py")))
    if args:
        selector = args[0]
        if selector.isdigit() and len(selector) == 1:
            selector = selector.zfill(2)
        folders = [p for p in folders if p.name.startswith(selector)]
        if not folders:
            sys.exit(f"No exercise starts with {args[0]}. Try 01 to 06.")
    passed = total = 0
    for folder in folders:
        number = folder.name.split("-", 1)[0]
        tool, reference = TOOLS.get(
            number, (folder.name.split("-", 1)[1], folder.name.split("-", 1)[1])
        )
        path = Path(args[1]).resolve() if len(args) > 1 else HERE.parent / "tools" / f"{reference}.py"
        if not path.is_file():
            sys.exit(f"Tool file not found: {path}")
        p, t = check(folder, path)
        passed, total = passed + p, total + t
    print(f"\n{passed} of {total} checks pass.")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
