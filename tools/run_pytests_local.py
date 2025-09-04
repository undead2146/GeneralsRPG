import pytest
import sys
with open('pytest_full.log','w',encoding='utf-8') as f:
    rc = pytest.main(['-vv','--maxfail=999'], plugins=[], stdout=f)
print('pytest exit code', rc)
sys.exit(rc)
