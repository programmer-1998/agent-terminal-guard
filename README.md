# Agent Terminal Guard (`atg`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-brightgreen.svg)](#)

Agent Terminal Guard (`atg`) is a lightweight watchdog and wrapper utility designed specifically for AI coding agents (such as Google Antigravity, Claude Code, Cursor, Aider, AutoGPT, and OpenCode).

It completely prevents agents from freezing indefinitely when executing terminal commands that prompt for user input (e.g. `sudo` password, `[y/n]` questions), get stuck in silent loops, or hit network deadlocks.

---

## 🎯 The Core Problem

When an autonomous AI agent executes a command in a headless environment:
1. **Interactive Stdin Blocking**: Commands like `sudo apt install`, `git push`, or `npm init` wait for keystrokes or passwords. Without an interactive user terminal, the process sits idle forever.
2. **Silent Loop / 404 Hangs**: Watchers, dead server pollings, or network hangs emit no output for hours, consuming CPU and freezing agent workflows.
3. **No Native Feedback**: The agent cannot diagnose why the execution never finished unless the user manually intervenes and kills the task.

---

## ⚡ How It Works

Agent Terminal Guard executes commands inside an isolated **Pseudo-Terminal (`pty`)** and inspects output streams in real time:

- **Regex Prompt Interceptor**: Instantly catches password requests (`[sudo] password`, `passphrase`), confirmations (`[y/n]`, `Do you want to continue`), and prompts. It halts the process immediately with exit code `125` and prints an explicit error reason.
- **Silence Watchdog**: Kills commands that produce zero output for longer than the silence threshold (`--silence`, default 20s).
- **Hard Max Timeout**: Prevents runaway builds or infinite loops (`--timeout`, default 60s).
- **Auto Non-Interactive Environment**: Injects `CI=1`, `DEBIAN_FRONTEND=noninteractive`, `GIT_TERMINAL_PROMPT=0`, and `PIP_NO_INPUT=1`.
- **Clean Actionable Guidance**: Injects structured recommendations directly into stderr so the AI agent knows how to self-correct without user intervention.

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/programmer-1998/agent-terminal-guard.git
cd agent-terminal-guard
pip install -e .
```

### CLI Usage

```bash
# Basic execution
atg "npm test"

# With custom hard timeout and silence threshold
atg -t 90 -s 15 "cargo build --release"

# Direct python invocation
python3 terminal_guard.py -t 60 -s 20 "echo 'Hello World'"
```

---

## 🧪 Testing

Run the included unit tests:

```bash
python3 test_guard.py
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
