import importlib, sys, traceback, inspect, os
sys.path.insert(0, os.path.abspath('.'))
out=[]
try:
    m = importlib.import_module('adventure.adventureset')
    out.append(f'module file: {getattr(m,"__file__",None)}')
    cls = getattr(m, 'AdventureSetCommands', None)
    out.append(f'AdventureSetCommands present: {cls is not None}')
    if cls:
        attr = getattr(cls, 'commands_adventureset_economy', None)
        out.append(f'attr type: {type(attr)}')
        out.append(f'has .command: {hasattr(attr, "command")}')
        try:
            out.append('repr attr: ' + repr(attr))
        except Exception as e:
            out.append('repr failed: ' + str(e))
        try:
            out.append('dir attr sample: ' + str([x for x in dir(attr) if not x.startswith('__')][:30]))
        except Exception as e:
            out.append('dir failed: ' + str(e))
except Exception as e:
    out.append('EXC:')
    out.append(str(e))
    out.append(traceback.format_exc())
with open('inspect_out.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n'.join(out))
