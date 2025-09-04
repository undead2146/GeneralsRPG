# -*- coding: utf-8 -*-
import logging
import re
import time
from typing import Literal, Union

import discord
from beautifultable import ALIGN_CENTER, BeautifulTable
from redbot.core import commands
from redbot.core.errors import BalanceTooHigh
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number

# Prefer the core economy implementation for logic, with a compatibility
# fallback to the command-layer shim during the refactor or in minimal test
# environments.
try:
    from adventure.core.economy import *  # noqa: F401,F403
    __all__ = ["add_cp", "remove_cp", "EconomyCommands"]
except Exception:  # pragma: no cover - fallback for minimal environments
    from adventure.commands.economy import *  # noqa: F401,F403
    __all__ = ["EconomyCommands"]
from .helpers import escape, has_separated_economy, smart_embed
