import os, sys
print('cwd=', os.getcwd())
print('sys.path[0]=', sys.path[0])
print('first 10 sys.path entries:')
for p in sys.path[:10]:
    print('  ', p)
try:
    import redbot
    print('redbot imported from', getattr(redbot, '__file__', repr(redbot)))
    import redbot.core
    print('redbot.core imported from', getattr(redbot.core, '__file__', repr(redbot.core)))
except Exception as e:
    print('import failed:', type(e), e)
