# -*- coding: utf-8 -*-
import contextlib
import logging
import os
from typing import Union

import discord
from beautifultable import ALIGN_LEFT, BeautifulTable
import importlib
import sys
import types

# Prefer the module object for redbot.core.commands so we can monkeypatch
# its attributes reliably. Some test setups put a mock `redbot.core` module
# in sys.modules where `commands` may be an attribute instead of a proper
# module; importing the submodule ensures we get the module object.
try:
    commands = importlib.import_module("redbot.core.commands")
except Exception:
    # Fallback: try to get it from sys.modules or create a minimal shim
    commands = sys.modules.get("redbot.core.commands")
    if commands is None:
        commands = types.ModuleType("redbot.core.commands")
        sys.modules["redbot.core.commands"] = commands

"""Compatibility shim for adventureset commands.

Implementation has been moved under :mod:`adventure.commands.adventureset` as
part of the refactor into `commands/`. Keep the top-level module as a
re-export so existing imports continue to work.
"""

try:
    from adventure.core.adventureset import *  # noqa: F401,F403
    __all__ = [name for name in dir() if not name.startswith("_")]
except Exception:  # pragma: no cover - fallback for environments without core
    from adventure.commands.adventureset import *  # noqa: F401,F403
    __all__ = [name for name in dir() if not name.startswith("_")]
