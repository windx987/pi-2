# Project structure

What is in the `python` branch, and where you work.

<p align="center"><img alt="Project structure of the python branch, in four sections: the agent, your work, read and run, outside the workshop. pi2/ holds the agent, one file per part (cli.py, tui.py, session.py, agent_loop.py, model_runtime.py, ai.py, schema.py, compaction.py, windows.py, extensions.py). exercises/ holds your extensions 01-read to 04-edit and 05-subagent, each with a README and checks, and check.py, which runs the checks; examples/ has hello.py and permission_gate.py; playground/ has what the agent works on: a failing test and 30 incident reports; pi2.py starts it; docs/ explains setup, connecting a model, a request step by step, compaction and this structure. pyproject.toml and assets/ are outside the workshop path." src="../assets/diagrams/python-structure.svg" width="760"></p>

The four sections are the agent, your work, what you read and run, and what the workshop does not need. In the agent, the files have the colors of Pi's packages: blue for the app (coding-agent), purple for the loop (agent), green for what talks to the model (ai). You work in red: your extensions, their checks, and a copy of the [playground](../playground/).
