import subprocess, sys, os
print('Running pytest with PYTHONPATH set to repo root...')
ROOT = os.path.abspath(os.path.dirname(__file__))
env = os.environ.copy()
env['PYTHONPATH'] = ROOT + os.pathsep + env.get('PYTHONPATH','')
proc = subprocess.run([sys.executable, '-m', 'pytest', '-r', 'a', '--maxfail=1'], capture_output=True, text=True, env=env)
with open('pytest_run.log', 'w', encoding='utf-8') as f:
    f.write(proc.stdout)
    f.write('\n')
    f.write(proc.stderr)
print('pytest exitcode=', proc.returncode)
print('Wrote pytest_run.log')
