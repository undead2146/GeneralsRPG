# small helper to run pytest and write a log file
import subprocess
import sys
import os

py = sys.executable
print('Using python:', py)
proc = subprocess.run([py, '-m', 'pytest', '-q', '--maxfail=999', '-vv'], capture_output=True)
out = proc.stdout + proc.stderr
with open('pytest_run.log', 'wb') as f:
    f.write(out)
print('Exit code', proc.returncode)
