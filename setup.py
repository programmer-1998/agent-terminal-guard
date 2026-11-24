from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-terminal-guard",
    version="0.1.0",
    author="Sina Khanzadeh",
    author_email="khanzadeh.1377@gmail.com",
    description="Intelligent Non-Blocking Terminal Watchdog for AI Coding Agents (Antigravity, Claude Code, Cursor, Aider)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/programmer-1998/agent-terminal-guard",
    packages=find_packages(),
    py_modules=["terminal_guard"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "atg=terminal_guard:main",
            "terminal-guard=terminal_guard:main",
        ],
    },
)
