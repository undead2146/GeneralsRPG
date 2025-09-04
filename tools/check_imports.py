import importlib.util, sys

spec = importlib.util.find_spec('adventure')
print('adventure spec:', spec)
if spec:
    print('adventure origin:', spec.origin)
    try:
        m = importlib.import_module('adventure')
        print('adventure package file:', getattr(m, '__file__', None))
    except Exception as e:
        print('import adventure failed:', type(e), e)

spec_r = importlib.util.find_spec('redbot')
print('redbot spec:', spec_r)
if spec_r:
    print('redbot origin:', spec_r.origin)
else:
    print('redbot not found')

print('sys.path[0:5]=')
for p in sys.path[:5]:
    print('  ', p)
