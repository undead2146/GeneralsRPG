from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Dict, List, Literal, MutableMapping, Optional, Tuple, Union

import discord
try:
    from redbot.core import Config, commands
    from redbot.core.bot import Red
except Exception:  # pragma: no cover - provide minimal fallbacks for test environments
    class Config:
        def __init__(self, *a, **k):
            pass

    class commands:
        class Cog:
            pass

        class Bot:
            pass

    class Red(commands.Bot):
        pass

if TYPE_CHECKING:
    from adventure.adventureresult import AdventureResults
    from adventure.adventureset import TaxesConverter
    from adventure.charsheet import Character, Item
    from adventure.constants import Rarities, Treasure
    from adventure.converters import (
        BackpackFilterParser,
        DayConverter,
        EquipableItemConverter,
        EquipmentConverter,
        ItemConverter,
        ItemsConverter,
        PercentageConverter,
        RarityConverter,
        SlotConverter,
        Stats,
        ThemeSetMonterConverter,
        ThemeSetPetConverter,
    )
    from adventure.game_session import GameSession
    from adventure.rng import Random
    from adventure.types import Monster


class AdventureMixin(ABC):
    """Type-hinting mixin used by the Adventure cog and its split modules.

    This keeps attribute definitions available for static analysis while the
    implementation moves into smaller modules.
    """

    def __init__(self, *_args):
        self.config: Config
        self.bot: Red
        self._adv_results: AdventureResults
        self.settings: Dict[Any, Any]
        self.emojis: SimpleNamespace
        self._ready: asyncio.Event
        self._adventure_countdown: dict
        self._rewards: dict
        self._reward_message: dict
        self._loss_message = {}
        self._trader_countdown = {}
        self._current_traders = {}
        self._curent_trader_stock = {}
        self._sessions: MutableMapping[int, GameSession] = {}
        self._react_messaged = []
        self._daily_bonus: dict = {}
        self.tasks = {}
        self.locks: MutableMapping[int, asyncio.Lock] = {}
        self.gb_task = None

        self.RAISINS: list = None
        self.THREATEE: list = None
        self.TR_GEAR_SET: dict = None
        self.ATTRIBS: dict = None
        self.MONSTERS: dict = None
        self.AS_MONSTERS: dict = None
        self.MONSTER_NOW: dict = None
        self.LOCATIONS: list = None
        self.PETS: dict = None
        self.EQUIPMENT: dict = None
        self.MATERIALS: dict = None
        self.PREFIXES: dict = None
        self.SUFFIXES: dict = None
        self._repo: str
        self._commit: str

    # The full list of abstract methods is intentionally omitted here; the
    # top-level shim will re-export the original module while we migrate code
    # into smaller files under adventure.core.
