import sys, os
print('cwd=', os.getcwd())
print('sys.path[0]=', sys.path[0])
print('\n'.join(sys.path[:10]))
try:
    import redbot
    print('redbot imported from', getattr(redbot, '__file__', 'built-in'))
    import redbot.core
    print('redbot.core imported from', getattr(redbot.core, '__file__', 'module'))
except Exception as e:
    print('import failed:', type(e), e)
