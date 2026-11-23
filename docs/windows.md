# pi/2 for Python on Windows

pi2 runs in PowerShell on Windows, with the same exercises and checks. This guide is the [Getting started](../README.md#getting-started) steps with Windows commands, and how to read the guides' macOS and Linux commands on Windows.

Tested on Windows 11 with PowerShell 5.1, Python 3.12, Git for Windows 2.56, Node.js 26 and Docker Desktop 29.

## 1. Python and Git

```powershell
winget install -e --id Python.Python.3.12
winget install -e --id Git.Git
```

Then open a new PowerShell window, so it finds them, and check:

```powershell
py --version        # Python 3.12 or newer (3.10 is enough)
git --version
```

Use `py`, not `python`. On many Windows machines `python` opens the Microsoft Store, even after the install.

Git for Windows also brings Git Bash, which the no-Docker mode of exercise 03 uses (step 4).

## 2. The code

```powershell
git clone -b python https://github.com/windx987/pi-2.git $HOME\pi-2
cd $HOME\pi-2
py pi2.py --version
```

It should print `0.1.0`. The guides write the clone as `~/pi-2`; in PowerShell it is `$HOME\pi-2`.

## 3. A model

The same `models.json` as on macOS and Linux ([the example](../README.md#3-a-model)), in your user folder:

```powershell
New-Item -ItemType Directory -Force $HOME\.pi\agent
notepad $HOME\.pi\agent\models.json
```

Paste the example, put in your server's values, and save. The file holds your key: keep it out of shared folders.

## 4. Docker, or the no-Docker mode (for exercise 03)

The choice is the same as in [the main guide](../README.md#4-docker-or-the-no-docker-mode-for-exercise-03): Docker isolates the commands the model writes, and the no-Docker mode runs them on your machine.

**Option 1: Docker Desktop (recommended)**

```powershell
winget install -e --id Docker.DockerDesktop
```

Start Docker Desktop from the Start menu and wait until it says it is running. Then pull the image once and try it:

```powershell
docker pull node:22-bookworm-slim
docker run --rm node:22-bookworm-slim node --version
```

**Option 2: no Docker**

```powershell
winget install -e --id OpenJS.NodeJS.LTS
```

Open a new PowerShell window, then check that the playground's tests run:

```powershell
node --version      # v22 or newer
cd $HOME\pi-2\playground
npm test            # pass 1, fail 1
```

If PowerShell says running scripts is disabled, run `npm.cmd test` instead: it is the same npm, without the PowerShell script.

Turn the mode on for this window:

```powershell
$env:PI2_NO_DOCKER = "1"
```

The commands then run in Git Bash, on your machine, in the working directory: not in `C:\Windows\System32\bash.exe`, which is WSL's Linux. They can reach your files and your network, so work only in the playground copy and load [the permission gate](../examples/permission_gate.py) with your tools. `Remove-Item env:PI2_NO_DOCKER` turns the mode off.

## 5. Start pi2

```powershell
cd $HOME\pi-2
py pi2.py -e examples\hello.py
```

For the exercises, copy the playground once and start pi2 from the copy:

```powershell
Copy-Item -Recurse $HOME\pi-2\playground $HOME\pi-workshop
cd $HOME\pi-workshop
py $HOME\pi-2\pi2.py -e $HOME\pi-2\exercises\01-read\read.py
```

Windows Terminal, the default on Windows 11, shows the colors and boxes; the older console windows do too. ctrl+c stops the agent. To exit, type `/quit`, or ctrl+z then Enter (ctrl+d on macOS and Linux).

## Reading the guides on Windows

The exercise guides show macOS and Linux commands. In PowerShell:

| Guide | PowerShell |
|---|---|
| `python3 ~/pi-2/pi2.py -e ~/pi-2/exercises/01-read/read.py` | `py $HOME\pi-2\pi2.py -e $HOME\pi-2\exercises\01-read\read.py` |
| `python3 ~/pi-2/exercises/check.py 01` | `py $HOME\pi-2\exercises\check.py 01` |
| `PI2_NO_DOCKER=1 python3 ...` | `$env:PI2_NO_DOCKER = "1"`, then `py ...` |
| `cp -R ~/pi-2/playground ~/pi-workshop` | `Copy-Item -Recurse $HOME\pi-2\playground $HOME\pi-workshop` |
| `rm -rf ~/pi-workshop` | `Remove-Item -Recurse -Force $HOME\pi-workshop` |
| `\` at the end of a line | `` ` `` (backtick) at the end of a line |

Write `$HOME`, not `~`: PowerShell does not turn `~` into your folder in the arguments of `py`.

The commands the agent runs with the bash tool stay bash commands, such as `npm test`: they run in the container or in Git Bash.

## What is different on Windows

- **Stopping a command.** On macOS and Linux, `proc.terminate()` sends a signal that `docker run` passes on to the container. On Windows it ends one process at once, which would leave the container running. [pi2/windows.py](../pi2/windows.py) runs the command under a watchdog that removes the container and the commands it started. Your `execute()` in exercise 03 stays the same, and the checks test it on Windows too.
- **Keys typed while the agent works** show on the screen; on macOS and Linux they are hidden until the next editor. They still wait for the next message.
- **Sessions** are saved in `$HOME\.pi\agent\python-sessions`.
