# minimal get_dict_converter stub used by adventureset
from typing import Callable

def get_dict_converter(delims=None) -> Callable:
    def _convert(value: str):
        # parse simple comma/space separated key,value pairs
        out = {}
        parts = [p for p in value.replace(';', ',').split(',') if p.strip()]
        for p in parts:
            if ':' in p:
                k, v = p.split(':', 1)
            elif ' ' in p:
                k, v = p.split(' ', 1)
            else:
                continue
            out[k.strip()] = v.strip()
        return out

    return _convert
