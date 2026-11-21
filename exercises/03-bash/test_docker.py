# Checks for exercise 03 in a real container. Run with the others: python3 exercises/check.py 03
#
# They need Docker running and the image pulled once (docker pull node:22-bookworm-slim). Without
# Docker, check.py skips this file and says so; test_bash.py still checks your process handling.

import os
import subprocess
import time

from check import Workspace, call, error_of, load_tool

NEEDS_DOCKER = True  # check.py skips this file when Docker is not running
IMAGE = "node:22-bookworm-slim"
TIMEOUT = 2


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


class DockerTest(Workspace):
    def setUp(self):
        super().setUp()
        no_docker = os.environ.pop("PI2_NO_DOCKER", None)  # these checks are for the real container
        if no_docker is not None:
            self.addCleanup(os.environ.__setitem__, "PI2_NO_DOCKER", no_docker)
        self.bash = load_tool("bash")
        self.before = running_containers()
        self.addCleanup(self.remove_leftovers)

    def remove_leftovers(self):
        """A failed check must not leave `sleep 30` running for the next one."""
        leftover = running_containers() - self.before
        if leftover:
            subprocess.run(["docker", "kill", *leftover], capture_output=True)

    def test_1_sees_the_workspace(self):
        """Step 1 (Docker): the command runs in a container that sees ctx.cwd at /workspace."""
        (self.cwd / "marker.txt").write_text("found me\n")
        text = call(self.bash, {"command": "pwd; cat marker.txt"}, self.cwd)
        self.assertIn("/workspace", text, f"the command should run in /workspace: {text.strip()[:200]}")
        self.assertIn("found me", text, f"the container does not see ctx.cwd; Docker shares only some folders: {text.strip()[:200]}")

    def test_3_timeout_comes_back(self):
        """Step 3 (Docker): sleep 30 with a 2 second timeout comes back soon, as an error that says so."""
        started = time.monotonic()
        error = error_of(self.bash, {"command": "sleep 30", "timeout": TIMEOUT}, self.cwd)
        seconds = time.monotonic() - started
        self.assertLess(seconds, TIMEOUT + 8, f"the tool returned after {seconds:.0f} s; stop the process at the timeout")
        self.assertRegex(str(error).lower(), "stop|time", f"say that the command was stopped: {error}")

    def test_3_timeout_leaves_no_container(self):
        """Step 3 (Docker): after the timeout, no container keeps running."""
        try:
            error_of(self.bash, {"command": "sleep 30", "timeout": TIMEOUT}, self.cwd)
        except AssertionError:
            pass  # it returned instead of raising: the check above says so; this one is about the container
        leftover = wait_for_leftovers(self.before)
        self.assertFalse(leftover, "the container still ran `sleep 30` (now removed): the docker client got SIGKILL, "
                                   "which it cannot pass on. Stop the process with proc.terminate() (SIGTERM).")
