import importlib.util, importlib, sys, os
out = []
out.append('cwd=' + os.getcwd())
out.append('sys.path[0]=' + sys.path[0])
out.append('sys.path (first 10):')
for p in sys.path[:10]:
    out.append('  ' + str(p))
spec = importlib.util.find_spec('adventure')
out.append('find_spec(adventure)=' + str(spec))
if spec:
    out.append('spec.origin=' + str(spec.origin))
try:
    m = importlib.import_module('adventure')
    out.append('imported adventure; __file__=' + str(getattr(m, '__file__', None)))
    out.append('adventure.__path__=' + str(getattr(m, '__path__', None)))
    try:
        sub = importlib.import_module('adventure.adventure')
        out.append('imported adventure.adventure; __file__=' + str(getattr(sub, '__file__', None)))
    except Exception as e:
        out.append('import adventure.adventure failed: ' + repr(e))
except Exception as e:
    out.append('import adventure failed: ' + repr(e))
# list local files
out.append('\nlocal files in cwd:')
for name in sorted(os.listdir('.')):
    out.append('  ' + name)
with open('inspect_output.log', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Wrote inspect_output.log')
