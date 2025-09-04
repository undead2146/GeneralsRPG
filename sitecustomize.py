import sys
import os
import types

# Ensure repository root (this file's directory) is on sys.path early so tests and imports
# can find repo-local stub packages (for environments where PYTHONPATH isn't set).
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

# --- Test-time shims: provide minimal redbot/core.commands.group-like decorator and
# the redbot.vendored.discord.ext.menus module early so imports that evaluate
# decorators at import-time won't fail during pytest collection.
try:
    # group-like shim returns an object with .command and .group to support
    # patterns like @commands.group() / @adventureset.group(...) and
    # subsequent @adventureset_locks.command(...)
    if "redbot.core.commands" not in sys.modules:
        core_cmds = types.ModuleType("redbot.core.commands")

        class _GroupShim:
            def __init__(self, func):
                self._func = func

            def command(self, *a, **k):
                def _decor(f):
                    return f

                return _decor

            def group(self, *a, **k):
                return self.command(*a, **k)

            def __call__(self, *a, **k):
                return self._func(*a, **k)

        def _group(*a, **k):
            def _decor(f):
                return _GroupShim(f)

            return _decor

        core_cmds.group = _group
        core_cmds.hybrid_group = _group
        core_cmds.Cog = type("Cog", (), {})
        core_cmds.Greedy = list
        # Attach a minimal redbot.core module that exposes 'commands'
        if "redbot.core" not in sys.modules:
            core_mod = types.ModuleType("redbot.core")
            core_mod.commands = core_cmds
            sys.modules["redbot.core"] = core_mod
        else:
            # ensure attribute is present
            setattr(sys.modules["redbot.core"], "commands", core_cmds)
        sys.modules["redbot.core.commands"] = core_cmds

    # vendored menus shim used by adventure.menus
    if "redbot.vendored.discord.ext.menus" not in sys.modules:
        menus_mod = types.ModuleType("redbot.vendored.discord.ext.menus")

        class _PageSource:
            def __init__(self, entries=None, per_page=10):
                self.entries = entries or []
                self.per_page = per_page

            def is_paginating(self):
                return bool(self.entries)

            def get_max_pages(self):
                if not self.entries:
                    return 0
                return (len(self.entries) + self.per_page - 1) // self.per_page

        class _MenuPages:
            def __init__(self, source=None):
                self.source = source
                self.current_page = 0

        menus_mod.ListPageSource = _PageSource
        menus_mod.MenuPages = _MenuPages
        # ensure parent packages exist so importlib finds the module path
        if "redbot.vendored" not in sys.modules:
            sys.modules["redbot.vendored"] = types.ModuleType("redbot.vendored")
        if "redbot.vendored.discord" not in sys.modules:
            sys.modules["redbot.vendored.discord"] = types.ModuleType("redbot.vendored.discord")
        if "redbot.vendored.discord.ext" not in sys.modules:
            ext_mod = types.ModuleType("redbot.vendored.discord.ext")
            sys.modules["redbot.vendored.discord.ext"] = ext_mod
        else:
            ext_mod = sys.modules["redbot.vendored.discord.ext"]
        # also expose the submodule as an attribute on the parent package so
        # `from redbot.vendored.discord.ext import menus` resolves correctly.
        setattr(ext_mod, 'menus', menus_mod)
        sys.modules["redbot.vendored.discord.ext.menus"] = menus_mod
except Exception:
    # Do not let sitecustomize crash imports; silently continue to keep test runner alive
    pass

# Ensure project root is on sys.path so local test stubs (e.g., 'redbot' package) are importable
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
