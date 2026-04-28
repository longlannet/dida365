#!/usr/bin/env python3
"""Compatibility wrapper for SKILL.md: add a Dida365 task."""
import argparse
import subprocess
import sys
from pathlib import Path

script = Path(__file__).with_name("dida.py")
parser = argparse.ArgumentParser()
parser.add_argument("title")
parser.add_argument("--content")
parser.add_argument("--due")
parser.add_argument("--project")
parser.add_argument("--priority", default="0")
parser.add_argument("--remind", action="store_true")
parser.add_argument("--remind-before")
parser.add_argument("--repeat")
parser.add_argument("--subtasks")
args = parser.parse_args()
cmd = [sys.executable, str(script), "add", args.title, "--priority", str(args.priority)]
for flag in ["content", "due", "project", "remind_before", "repeat", "subtasks"]:
    value = getattr(args, flag)
    if value:
        cmd += ["--" + flag.replace("_", "-"), value]
if args.remind:
    cmd.append("--remind")
raise SystemExit(subprocess.call(cmd))
