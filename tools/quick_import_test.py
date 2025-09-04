import sys, os
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
print('sys.path[0]=', sys.path[0])
try:
    import adventure.loot as lootmod
    print('adventure.loot imported:', lootmod)
    print('Character in loot module:', getattr(lootmod, 'Character', None))
except Exception as e:
    print('import failed:', type(e), e)
    import traceback; traceback.print_exc()
