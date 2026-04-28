#!/usr/bin/env python3
"""Compatibility wrapper for SKILL.md: list Dida365 tasks."""
import argparse
import subprocess
import sys
from pathlib import Path

script = Path(__file__).with_name("dida.py")
parser = argparse.ArgumentParser()
parser.add_argument("--project")
args = parser.parse_args()
cmd = [sys.executable, str(script), "list"]
if args.project:
    cmd += ["--project", args.project]
raise SystemExit(subprocess.call(cmd))
