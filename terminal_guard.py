#!/usr/bin/env python3
"""
Agent Terminal Guard (ATG) / safe-exec
======================================
Robust non-blocking CLI executor and watchdog for AI Coding Agents
(Antigravity, Claude Code, Cursor, Aider, OpenCode, AutoGPT).

Features:
- PTY (Pseudo-Terminal) allocation: catches interactive prompts even when piped
- Real-time Regex Interceptor: detects sudo/password, auth passphrases, [y/n] questions
- Silence Watchdog (Idle Hang Detection): kills frozen processes with no output
- Hard Execution Timeout: prevents infinite compilation/loops
- Non-Interactive Environment auto-injection (CI=1, DEBIAN_FRONTEND=noninteractive, GIT_TERMINAL_PROMPT=0)
- Graceful termination: SIGTERM -> SIGKILL on process group
- Structured Machine-Readable & Clean Human Output: outputs actionable reason for LLM agents
"""

import sys
import os
import pty
import select
import signal
import time
import re
import argparse
import subprocess

# Common interactive prompts that cause AI agents to freeze indefinitely
PROMPT_PATTERNS = [
    (re.compile(r"\[sudo\]\s+password\s+for", re.IGNORECASE), "Sudo password required (privileged execution blocked)"),
    (re.compile(r"password\s*:", re.IGNORECASE), "Password input prompt detected"),
    (re.compile(r"enter\s+(?:passphrase|password)", re.IGNORECASE), "Passphrase/Password prompt detected"),
    (re.compile(r"do\s+you\s+want\s+to\s+continue\s*\[\s*[yY]/[nN]\s*\]", re.IGNORECASE), "Interactive Y/N confirmation required"),
    (re.compile(r"\(y/n\)\s*\?", re.IGNORECASE), "Interactive (y/n) confirmation required"),
    (re.compile(r"are\s+you\s+sure\s+you\s+want\s+to\s+continue", re.IGNORECASE), "Interactive confirmation prompt detected"),
    (re.compile(r"press\s+\[?enter\]?\s+to\s+continue", re.IGNORECASE), "Interactive Enter key required"),
    (re.compile(r"select\s+an\s+option", re.IGNORECASE), "Interactive menu selection prompt detected"),
    (re.compile(r"username\s*for\s*['\"].*?['\"]\s*:", re.IGNORECASE), "Authentication credentials (username) required"),
]

def kill_process_group(pgid):
    """Safely kill an entire process group."""
    try:
        os.killpg(pgid, signal.SIGTERM)
        time.sleep(0.5)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass

def safe_run(command, max_time=120, silence_timeout=25, raw_output=True):
    """
    Executes command inside a pseudo-terminal (PTY) with active watchdog inspection.
    """
    env = os.environ.copy()
    env.update({
        "CI": "1",
        "DEBIAN_FRONTEND": "noninteractive",
        "GIT_TERMINAL_PROMPT": "0",
        "PIP_NO_INPUT": "1",
        "PYTHONUNBUFFERED": "1",
        "TERM": "xterm-256color",
        "FORCE_COLOR": "0",
        "PAGER": "cat",
    })

    master_fd, slave_fd = pty.openpty()

    start_time = time.time()
    last_output_time = time.time()
    collected_bytes = bytearray()
    termination_reason = None
    exit_code = 0

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid,  # Create distinct process group
            env=env,
            close_fds=True
        )
        os.close(slave_fd)  # Closed in parent, open in child

        pgid = os.getpgid(proc.pid)

        while True:
            # Check hard max timeout
            elapsed = time.time() - start_time
            if max_time and elapsed > max_time:
                termination_reason = f"Max execution timeout reached ({max_time}s limit exceeded)"
                kill_process_group(pgid)
                exit_code = 124
                break

            # Check silence / idle timeout
            idle_time = time.time() - last_output_time
            if silence_timeout and idle_time > silence_timeout:
                termination_reason = f"Silence timeout ({silence_timeout}s elapsed with zero output/hang)"
                kill_process_group(pgid)
                exit_code = 124
                break

            # Poll PTY
            r, _, _ = select.select([master_fd], [], [], 0.5)

            if proc.poll() is not None:
                # Process finished naturally; drain remaining buffer
                while True:
                    r_drain, _, _ = select.select([master_fd], [], [], 0.1)
                    if not r_drain:
                        break
                    try:
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break
                        collected_bytes.extend(chunk)
                        if raw_output:
                            sys.stdout.buffer.write(chunk)
                            sys.stdout.flush()
                    except OSError:
                        break
                exit_code = proc.returncode
                break

            if r:
                try:
                    chunk = os.read(master_fd, 4096)
                    if not chunk:
                        continue
                    collected_bytes.extend(chunk)
                    last_output_time = time.time()

                    if raw_output:
                        sys.stdout.buffer.write(chunk)
                        sys.stdout.flush()

                    # Check tail of text for prompts
                    # Decoding safely ignoring invalid utf8
                    recent_text = collected_bytes[-2048:].decode("utf-8", errors="ignore")

                    prompt_found = False
                    for pattern, desc in PROMPT_PATTERNS:
                        if pattern.search(recent_text):
                            termination_reason = desc
                            kill_process_group(pgid)
                            exit_code = 125
                            prompt_found = True
                            break

                    if prompt_found:
                        break

                except OSError:
                    # EIO is expected on Linux when child closes slave
                    break

        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            kill_process_group(pgid)

    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass

    if termination_reason:
        warning_msg = (
            f"\n\n[GUARD-ABORT]: Command terminated by Agent Terminal Guard.\n"
            f"REASON: {termination_reason}\n"
            f"COMMAND: {command}\n"
            f"RECOMMENDATION FOR AGENT: Do not retry this command blindly. "
            f"If it needs root/sudo, ask user. If it's a daemon/server, run with backgrounding (& / IsDaemon). "
            f"If interactive, pass non-interactive flags (-y, --yes, --non-interactive).\n"
        )
        sys.stderr.write(warning_msg)
        sys.stderr.flush()

    return exit_code

def main():
    parser = argparse.ArgumentParser(
        description="Agent Terminal Guard - Keep AI terminal executions from hanging or blocking."
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=60,
        help="Hard max execution timeout in seconds (default: 60s)"
    )
    parser.add_argument(
        "-s", "--silence",
        type=int,
        default=20,
        help="Silence timeout in seconds (kills process if no output for X seconds, default: 20s)"
    )
    parser.add_argument(
        "command",
        nargs="+",
        help="Command to execute securely"
    )

    args = parser.parse_args()
    full_cmd = " ".join(args.command)
    code = safe_run(full_cmd, max_time=args.timeout, silence_timeout=args.silence)
    sys.exit(code)

if __name__ == "__main__":
    main()
