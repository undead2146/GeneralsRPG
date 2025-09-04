def bold(x):
    return f"**{x}**"

def box(x, lang=None):
    return str(x)

def humanize_list(x):
    if isinstance(x, (list, tuple)):
        return ", ".join(str(i) for i in x)
    return str(x)

def humanize_number(x):
    try:
        return str(int(x))
    except Exception:
        return str(x)
