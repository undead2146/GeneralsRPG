# Minimal stub of beautifultable package used for tests
ALIGN_LEFT = 'left'
ALIGN_CENTER = 'center'

class _Border:
    def __init__(self):
        self.top = ''
        self.bottom = ''

class _Columns:
    def __init__(self):
        self.header = []
        self.width = None

class _Rows(list):
    def sort(self, *a, **k):
        try:
            super().sort(*a, **k)
        except Exception:
            pass

class BeautifulTable:
    STYLE_RST = 'rst'

    def __init__(self, default_alignment=None, maxwidth=None):
        self.default_alignment = default_alignment
        self.maxwidth = maxwidth
        self.columns = _Columns()
        self.rows = _Rows()
        self.border = _Border()

    def set_style(self, *a, **k):
        return None

    def __str__(self):
        # render rows simply
        out = []
        for r in self.rows:
            try:
                out.append(str(r))
            except Exception:
                out.append(repr(r))
        return "\n".join(out)
