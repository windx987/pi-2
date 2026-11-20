# Checks the timeout of your bash tool (EXERCISE 4): `sleep 30` with a 2 second timeout must come back
# as an error result that says the command was stopped, and leave no container running.
#
# Needs Docker running. From the repository root:
#   python3 exercises/03-bash/check_timeout.py                  # checks bash.py
#   python3 exercises/03-bash/check_timeout.py path/to/bash.py  # checks another file

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # the repository root, where the pi2 package is

from pi2 import ExtensionAPI, ToolContext  # noqa: E402

IMAGE = "node:22-bookworm-slim"
TIMEOUT = 2


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "bash.py"
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        sys.exit("Docker is not running. Start it (Docker Desktop, or `colima start`) and try again.")
    api = ExtensionAPI()
    api.load(str(path))
    if "bash" not in api.tools:
        sys.exit(f"{path} registers no tool named bash.")

    before = running_containers()
    # Under the home directory: Docker Desktop and Colima share it with their VM, /tmp may not be.
    workspace = tempfile.mkdtemp(dir=Path.home(), prefix="pi2-timeout-check-")
    started = time.monotonic()
    try:
        result, is_error = api.tools["bash"].execute({"command": "sleep 30", "timeout": TIMEOUT}, ToolContext(workspace)), False
    except NotImplementedError as error:
        sys.exit(f"Not implemented yet: {error}")
    except Exception as error:  # noqa: BLE001  (an exception is the tool's error result)
        result, is_error = str(error), True
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    seconds = time.monotonic() - started

    failures = [
        check(seconds < TIMEOUT + 8, f"returns soon after the timeout ({seconds:.1f} s)"),
        check(is_error, "the result is an error (the tool raised an exception)"),
        check(any(word in result.lower() for word in ("stop", "time")), f"the result says it was stopped: {result.strip()[-80:]!r}"),
    ]
    leftover = wait_for_leftovers(before)
    failures.append(check(not leftover, "no container left running"))
    if leftover:
        print("  The container still runs `sleep 30`: the docker client got SIGKILL, which it cannot pass on.")
        print("  Stop the process with proc.terminate() (SIGTERM) instead. Removing the leftover container now.")
        subprocess.run(["docker", "kill", *leftover], capture_output=True)
    print("\nAll checks passed." if not any(failures) else f"\n{sum(failures)} check(s) failed.")
    sys.exit(1 if any(failures) else 0)


def check(ok, label):
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return not ok


def running_containers():
    out = subprocess.run(["docker", "ps", "-q", "--filter", f"ancestor={IMAGE}"], capture_output=True, text=True).stdout
    return set(out.split())


def wait_for_leftovers(before):
    """Containers of the image that started during the check and still run after a few seconds."""
    for _ in range(10):
        leftover = running_containers() - before
        if not leftover:
            return leftover
        time.sleep(0.5)
    return leftover


if __name__ == "__main__":
    main()
