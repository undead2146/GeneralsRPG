"""Run pytest with the repository root on PYTHONPATH.

This script is intended to be invoked from the workspace root. It sets
PYTHONPATH to the repository root and runs pytest with the provided
arguments (or a sensible default).
"""
import os
import sys
import subprocess

repo_root = os.path.dirname(os.path.abspath(__file__))
env = os.environ.copy()
env["PYTHONPATH"] = repo_root

args = ["pytest", "-q", "--maxfail=1"] + sys.argv[1:]
print("Running:", " ".join(args))
print("PYTHONPATH=", env["PYTHONPATH"]) 

res = subprocess.run(args, env=env)
sys.exit(res.returncode)
