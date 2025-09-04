# -*- coding: utf-8 -*-
import os
import sys

# Ensure the repository root is on sys.path so local test stubs (e.g., `redbot`) are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Early package-level shims: ensure redbot/core.commands provides a group-like
# decorator and that vendored menus expose ListPageSource/MenuPages. This
# guarantees imports inside the adventure package won't fail at import time
# due to test-runner stubs that return plain functions.
try:
    import types
    # commands group shim
    rc = sys.modules.get("redbot.core")
    if rc is None or "redbot.core.commands" not in sys.modules:
        core_mod = types.ModuleType("redbot.core")
        cmds = types.ModuleType("redbot.core.commands")

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

        cmds.group = _group
        cmds.hybrid_group = _group
        cmds.Cog = type("Cog", (), {})
        core_mod.commands = cmds
        sys.modules["redbot.core"] = core_mod
        sys.modules["redbot.core.commands"] = cmds

    # vendored menus shim
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
        # ensure parent packages exist and register
        if "redbot.vendored" not in sys.modules:
            sys.modules["redbot.vendored"] = types.ModuleType("redbot.vendored")
        if "redbot.vendored.discord" not in sys.modules:
            sys.modules["redbot.vendored.discord"] = types.ModuleType("redbot.vendored.discord")
        if "redbot.vendored.discord.ext" not in sys.modules:
            sys.modules["redbot.vendored.discord.ext"] = types.ModuleType("redbot.vendored.discord.ext")
        sys.modules["redbot.vendored.discord.ext.menus"] = menus_mod
except Exception:
    pass

# If a local `redbot` stub exists in the repo, load it directly so tests can import it
try:  # pragma: no cover - test-time helper
    import importlib.util
    redbot_init = os.path.join(ROOT, "redbot", "__init__.py")
    if os.path.exists(redbot_init) and "redbot" not in sys.modules:
        spec = importlib.util.spec_from_file_location("redbot", redbot_init)
        redbot_mod = importlib.util.module_from_spec(spec)
        sys.modules["redbot"] = redbot_mod
        spec.loader.exec_module(redbot_mod)
        # attempt to load subpackage redbot.core if present
        core_init = os.path.join(ROOT, "redbot", "core", "__init__.py")
        if os.path.exists(core_init) and "redbot.core" not in sys.modules:
            spec = importlib.util.spec_from_file_location("redbot.core", core_init)
            core_mod = importlib.util.module_from_spec(spec)
            sys.modules["redbot.core"] = core_mod
            spec.loader.exec_module(core_mod)
except Exception:
    pass

try:
    from .adventure import Adventure
except Exception:
    # Defer importing Adventure at package import time to avoid import-time
    # errors during pytest collection. Tests that need the submodule will
    # import it directly.
    Adventure = None

__red_end_user_data_statement__ = (
    "This cog stores data provided by users "
    "for the express purpose of redisplaying. "
    "It does not store user data which was not "
    "provided through a command. "
    "Users may remove their own content "
    "without making a data removal request. "
    "This cog does not support data requests, "
    "but will respect deletion requests."
)


async def setup(bot):
    cog = Adventure(bot)
    await bot.add_cog(cog)
