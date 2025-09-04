"""Compatibility shim re-exporting UI menus from adventure.ui.menus.

The implementation now lives in :mod:`adventure.ui.menus`. Keep this module
as a thin re-export so external imports that reference ``adventure.menus``
continue to work during the refactor.
"""

from adventure.ui.menus import *  # noqa: F401,F403

# Backwards-compat exports expected by older importers. If the underlying
# `adventure.ui.menus` module is missing any of these names during the
# refactor, provide tiny placeholders so importers (and tests) don't fail at
# collection time.
__all__ = [
    "LeaderboardMenu",
    "LeaderboardSource",
    "BackpackMenu",
    "BackpackSource",
    "BaseMenu",
    "SimpleSource",
]

try:
    BaseMenu  # type: ignore
except Exception:
    # minimal placeholder used only for import-time stability
    class BaseMenu:
        def __init__(self, *a, **k):
            pass

try:
    SimpleSource  # type: ignore
except Exception:
    class SimpleSource:
        def __init__(self, entries=None):
            self.entries = entries or []
