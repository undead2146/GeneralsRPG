import traceback, importlib, inspect
p='z\\\\GeneralsRPG\\\\adventure\\\\adventure.py'
print('--- file head ---')
with open(p,'r',encoding='utf-8') as f:
    for i,line in enumerate(f):
        if i<80:
            print(f'{i+1:03}: {line.rstrip()}')
        else:
            break
print('\n--- attempting import adventure.adventure ---')
try:
    m=importlib.import_module('adventure.adventure')
    print('import ok, module file=', getattr(m,'__file__',None))
except Exception as e:
    print('import failed:', type(e), e)
    traceback.print_exc()
