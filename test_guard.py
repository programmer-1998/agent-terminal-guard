#!/usr/bin/env python3
import unittest
import subprocess
import os

GUARD_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "terminal_guard.py"))

class TestAgentTerminalGuard(unittest.TestCase):
    def test_normal_command(self):
        cmd = ["python3", GUARD_SCRIPT, "-t", "5", "echo 'Hello World'"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("Hello World", res.stdout)

    def test_sudo_prompt_abort(self):
        cmd = ["python3", GUARD_SCRIPT, "-t", "5", "-s", "3", "printf '[sudo] password for user: ' && sleep 5"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 125)
        self.assertIn("Sudo password required", res.stderr)

    def test_yes_no_prompt_abort(self):
        cmd = ["python3", GUARD_SCRIPT, "-t", "5", "-s", "3", "printf 'Do you want to continue [Y/n]? ' && sleep 5"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 125)
        self.assertIn("Interactive Y/N confirmation required", res.stderr)

    def test_silence_timeout(self):
        cmd = ["python3", GUARD_SCRIPT, "-t", "10", "-s", "2", "sleep 6"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 124)
        self.assertIn("Silence timeout", res.stderr)

    def test_max_timeout(self):
        # Continuous output to bypass silence timeout, but hit hard limit
        cmd = ["python3", GUARD_SCRIPT, "-t", "3", "-s", "5", "while true; do echo 'tick'; sleep 0.5; done"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 124)
        self.assertIn("Max execution timeout reached", res.stderr)

if __name__ == "__main__":
    unittest.main()
