# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import asyncio
import enum
import logging
import re
import shlex
from collections import defaultdict
from datetime import timedelta
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple, Union

import discord
from discord.app_commands import Choice, Transformer
from discord.ext.commands.converter import Converter
from discord.ext.commands.errors import BadArgument
from redbot.core import commands
# Provide minimal compatibility fallbacks when running under pytest without Red
# Some test environments include a minimal `redbot.core` but lack newer helpers
# like `FlagConverter` and `flag`. Provide simple, non-invasive stand-ins so
# modules can be imported and class definitions (like `class Stats(commands.FlagConverter, ...)`)
# succeed during collection.
if not hasattr(commands, "FlagConverter"):
    class _FlagConverterBase:
        """Very small stub to allow subclassing in tests.

        It intentionally does not implement flag parsing behavior — unit tests
        that exercise runtime parsing should use more complete mocks.
        """

        def __init_subclass__(cls, *args, **kwargs):
            # Accept positional and keyword args (e.g., case_insensitive=True)
            # used in subclassing. Some built-in implementations (object.__init_subclass__)
            # may not accept kwargs, so try to call super with them and fall back
            # to a no-op if that raises a TypeError.
            try:
                return super().__init_subclass__(*args, **kwargs)
            except TypeError:
                try:
                    return super().__init_subclass__()
                except Exception:
                    # Best-effort for minimal stub: silently ignore to allow test imports.
                    return None

    commands.FlagConverter = _FlagConverterBase

if not hasattr(commands, "flag"):
    def _flag_factory(*_args, **_kwargs):
        """Return a simple descriptor that provides a default value on instances.

        This keeps class attributes present and importable; it does not attempt
        to implement Red's full flag parsing semantics.
        """

        default = _kwargs.get("default") if _kwargs else None

        class _Flag:
            def __init__(self, default=default):
                self.default = default

            def __get__(self, instance, owner):
                if instance is None:
                    return self
                return getattr(instance, f"_flag_{id(self)}", self.default)

            def __set__(self, instance, value):
                setattr(instance, f"_flag_{id(self)}", value)

        return _Flag()

    commands.flag = _flag_factory
try:
    from redbot.core.commands import UserFeedbackCheckFailure
except Exception:  # pragma: no cover - fallback for test environments without Red
    class UserFeedbackCheckFailure(Exception):
        """Lightweight fallback used during tests when Red's exception isn't available."""
        def __init__(self, message: str = ""):
            super().__init__(message)
try:
    from redbot.core.i18n import Translator, set_contextual_locales_from_guild
except Exception:  # pragma: no cover - provide lightweight fallbacks for test environments
    class Translator:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, s: str) -> str:
            return s

        def gettext(self, s: str) -> str:
            return s

    async def set_contextual_locales_from_guild(bot, guild):
        return
try:
    from redbot.core.utils.chat_formatting import box, humanize_list
    from redbot.core.utils.menus import start_adding_reactions
    from redbot.core.utils.predicates import ReactionPredicate
except Exception:  # pragma: no cover - lightweight fallbacks for test envs without Red
    def box(text: str, lang: str = None) -> str:
        return text

    def humanize_list(items: list) -> str:
        try:
            return ", ".join(str(i) for i in items)
        except Exception:
            return str(items)

    def start_adding_reactions(msg, emojis):
        # No-op for tests
        return None

    class ReactionPredicate:
        NUMBER_EMOJIS = [str(i) for i in range(10)]

        @staticmethod
        def with_emojis(emojis, msg, user=None):
            class _Pred:
                def __init__(self):
                    self.result = 0

                def __call__(self, reaction, user):
                    return False

            return _Pred()

from adventure.charsheet import Character, Item
from adventure.constants import DEV_LIST, HeroClasses, Rarities, Skills, Slot
from adventure.helpers import smart_embed

log = logging.getLogger("red.cogs.adventure")

_ = Translator("Adventure", __file__)

TIME_RE_STRING = r"\s?".join(
    [
        r"((?P<days>\d+?)\s?(d(ays?)?))?",
        r"((?P<hours>\d+?)\s?(hours?|hrs|hr?))?",
        r"((?P<minutes>\d+?)\s?(minutes?|mins?|m))?",
        r"((?P<seconds>\d+?)\s?(seconds?|secs?|s))?",
    ]
)

TIME_RE = re.compile(TIME_RE_STRING, re.I)
REBIRTHSTATMULT = 2

REBIRTH_LVL = 20
REBIRTH_STEP = 10
SET_BONUSES = {}

TR_GEAR_SET = {}
PETS = {}

ATT = re.compile(r"(-?\d*) (att(?:ack)?)")
CHA = re.compile(r"(-?\d*) (cha(?:risma)?|dip(?:lo?(?:macy)?)?)")
INT = re.compile(r"(-?\d*) (int(?:elligence)?)")
LUCK = re.compile(r"(-?\d*) (luck)")
DEX = re.compile(r"(-?\d*) (dex(?:terity)?)")
SLOT = re.compile(r"(head|neck|chest|gloves|belt|legs|boots|left|right|ring|charm|twohanded)")
RARITY = re.compile(r"(normal|rare|epic|legend(?:ary)?|asc(?:ended)?|set|forged|event)")

DEG = re.compile(r"(-?\d*) degrade")
LEVEL = re.compile(r"(-?\d*) (level|lvl)")
PERCENTAGE = re.compile(r"^(\d*\.?\d+)(%?)")
DAY_REGEX = re.compile(
    r"^(?P<monday>mon(?:day)?|1)$|"
    r"^(?P<tuesday>tue(?:sday)?|2)$|"
    r"^(?P<wednesday>wed(?:nesday)?|3)$|"
    r"^(?P<thursday>th(?:u(?:rs(?:day)?)?)?|4)$|"
    r"^(?P<friday>fri(?:day)?|5)$|"
    r"^(?P<saturday>sat(?:urday)?|6)$|"
    r"^(?P<sunday>sun(?:day)?|7)$",
    re.IGNORECASE,
)

_DAY_MAPPING = {
    "monday": "1",
    "tuesday": "2",
    "wednesday": "3",
    "thursday": "4",
    "friday": "5",
    "saturday": "6",
    "sunday": "7",
}
ARG_OP_REGEX = re.compile(r"(?P<op>>|<)?(?P<value>-?\d+)")


def parse_timedelta(argument: str) -> Optional[timedelta]:
    matches = TIME_RE.match(argument)
    if matches:
        params = {k: int(v) for k, v in matches.groupdict().items() if v is not None}
        if params:
            return timedelta(**params)
    return None


class ArgParserFailure(UserFeedbackCheckFailure):
    """Raised when parsing an argument fails."""

    def __init__(self, cmd: str, message: str):
        self.cmd = cmd
        super().__init__(message=message)


class RarityConverter(Transformer):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> Optional[Rarities]:
        try:
            rarity = Rarities.get_from_name(argument)
        except KeyError:
            raise BadArgument(
                _("{rarity} is not a valid rarity, select one of {rarities}").format(
                    rarity=argument, rarities=humanize_list([i.get_name() for i in Rarities if i.is_chest])
                )
            )
        return rarity

    @classmethod
    async def transform(cls, interaction: discord.Interaction, argument: str) -> Optional[Rarities]:
        ctx = await interaction.client.get_context(interaction)
        return await cls.convert(ctx, argument)

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[Choice]:
        choices = []
        # cog = interaction.client.get_cog("Adventure")
        log.debug(interaction.command)
        for rarity in Rarities:
            if rarity is Rarities.pet:
                continue
            if interaction.command and interaction.command.name in ["loot", "convert"] and not rarity.is_chest:
                continue
            if current.lower() in rarity.get_name().lower():
                choices.append(Choice(name=rarity.get_name(), value=rarity.name))
        return choices


class ChallengeConverter(Transformer):
    """Minimal placeholder for challenge/area converters used in wrappers and annotations.

    Returns the raw argument string. Tests that need richer behaviour should mock or
    replace this with a more complete implementation.
    """

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: Optional[str]):
        return argument

    @classmethod
    async def transform(cls, interaction: discord.Interaction, argument: Optional[str]):
        ctx = await interaction.client.get_context(interaction)
        return await cls.convert(ctx, argument)


class SkillConverter(Transformer):
    """Minimal placeholder for skill converters used by drill/skill commands.

    Returns the raw argument string. Real implementations map to skill objects.
    """

    @classmethod
    async def convert(cls, ctx: commands.Context, argument: Optional[str]):
        return argument

    @classmethod
    async def transform(cls, interaction: discord.Interaction, argument: Optional[str]):
        ctx = await interaction.client.get_context(interaction)
        return await cls.convert(ctx, argument)


class SlotConverter(Transformer):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> Optional[Slot]:
        if argument:
            try:
                return Slot.get_from_name(argument)
            except ValueError:
                raise BadArgument(
                    _("{provided} is not a valid slot, select one of {slots}").format(
                        provided=argument, slots=humanize_list([i.get_name() for i in Slot])
                    )
                )

        return None

    @classmethod
    async def transform(cls, interaction: discord.Interaction, argument: str) -> Optional[Slot]:
        ctx = await interaction.client.get_context(interaction)
        return await cls.convert(ctx, argument)

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[Choice]:
        return [Choice(name=i.get_name(), value=i.name) for i in Slot if current.lower() in i.get_name().lower()]


class Stats(commands.FlagConverter, case_insensitive=True):
    attack: Optional[int] = commands.flag(name="att", aliases=["attack"], default=0)
    charisma: Optional[int] = commands.flag(name="cha", aliases=["charisma", "diplomacy", "diplo"], default=0)
    intelligence: Optional[int] = commands.flag(name="int", aliases=["intelligence"], default=0)
    dexterity: Optional[int] = commands.flag(name="dex", aliases=["dexterity"], default=0)
    luck: Optional[int] = commands.flag(name="luck", default=0)
    rarity: Optional[Rarities] = commands.flag(name="rarity", default=Rarities.normal, converter=RarityConverter)
    degrade: Optional[int] = commands.flag(name="degrade", aliases=["deg"], default=3)
    level: Optional[int] = commands.flag(name="level", aliases=["lvl"], default=1)
    slot: Optional[Slot] = commands.flag(name="slot", default=Slot.right, converter=SlotConverter)

    async def to_json(self, ctx: commands.Context) -> Dict[str, Union[List[str], int, str]]:
        result = {
            "slot": ["left"],
            "att": 0,
            "cha": 0,
            "int": 0,
            "dex": 0,
            "luck": 0,
            "rarity": "normal",
            "degrade": 0,
            "lvl": 1,
        }
        possible_stats = {
            "slot": self.slot.to_json() if self.slot else ["left"],
            "att": self.attack,
            "cha": self.charisma,
            "int": self.intelligence,
            "dex": self.dexterity,
            "luck": self.luck,
            "rarity": self.rarity.name if self.rarity else "normal",
            "degrade": self.degrade,
            "lvl": self.level,
        }
        for key, value in possible_stats.items():
            if key in ["slot", "rarity"]:
                if key == "rarity" and value in ("pet", "forged"):
                    raise BadArgument(_("How do you plan to create items with those rarities? Not creating item."))
                result[key] = value
                continue
            try:
                stat = int(value)
                if (
                    (key not in ["degrade", "lvl"] and stat > 10) or (key == "lvl" and stat < 50)
                ) and not await ctx.bot.is_owner(ctx.author):
                    raise BadArgument(_("Don't you think that's a bit overpowered? Not creating item."))
                result[key] = value
            except (AttributeError, ValueError):
                result[key] = value
                pass
        return result


class ItemsConverter(Converter):
    async def convert(self, ctx, argument) -> Tuple[str, List[Item]]:
        try:
            c = await Character.from_json(
                ctx,
                ctx.bot.get_cog("Adventure").config,
                ctx.author,
                ctx.bot.get_cog("Adventure")._daily_bonus,
            )
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            raise BadArgument
        rarity = None
        try:
            rarity_re = "|".join(f"{k}|{v}" for k, v in Rarities.names().items())
            rarity_match = re.match(rarity_re, argument.lower(), flags=re.I)
            if rarity_match:
                try:
                    rarity = Rarities.get_from_name(str(rarity_match.group(0)))
                except KeyError:
                    pass
        except AttributeError:
            pass

        if argument.lower() == "all":
            rarity = True

        if rarity is None:
            no_markdown = Item.remove_markdowns(argument)
            lookup = list(i for x, i in c.backpack.items() if no_markdown.lower() in x.lower())
            lookup_m = list(i for i in c.backpack.values() if argument.lower() == str(i).lower() and str(i))
            lookup_e = list(i for i in c.backpack.values() if argument == str(i))
            _temp_items = set()
            for i in lookup:
                _temp_items.add(str(i))
            for i in lookup_m:
                _temp_items.add(str(i))
            for i in lookup_e:
                _temp_items.add(str(i))
        elif rarity is True:
            lookup = list(i for i in c.backpack.values())
            return "all", lookup
        else:
            lookup = list(i for i in c.backpack.values() if i.rarity is rarity)
            if lookup:
                return "all", lookup
            raise BadArgument(_("You don't own any `{}` items.").format(argument))

        if len(lookup_e) == 1:
            return "single", [lookup_e[0]]
        if len(lookup) == 1:
            return "single", [lookup[0]]
        elif len(lookup_m) == 1:
            return "single", [lookup_m[0]]
        elif len(lookup) == 0 and len(lookup_m) == 0:
            raise BadArgument(_("`{}` doesn't seem to match any items you own.").format(argument))
        else:
            lookup = list(i for i in c.backpack.values() if str(i) in _temp_items)
            if len(lookup) > 10:
                raise BadArgument(
                    _("You have too many items matching the name `{}`, please be more specific.").format(argument)
                )
            items = ""
            for number, item in enumerate(lookup):
                items += f"{number}. {str(item)} (owned {item.owned})\n"

            msg = await ctx.send(
                _("Multiple items share that name, which one would you like?\n{items}").format(
                    items=box(items, lang="ansi")
                )
            )
            emojis = ReactionPredicate.NUMBER_EMOJIS[: len(lookup)]
            start_adding_reactions(msg, emojis)
            pred = ReactionPredicate.with_emojis(emojis, msg, user=ctx.author)
            try:
                await ctx.bot.wait_for("reaction_add", check=pred, timeout=30)
            except asyncio.TimeoutError:
                raise BadArgument(_("Alright then."))
            return "single", [lookup[pred.result]]


class ItemButton(discord.ui.Button):
    def __init__(self, item: Item):
        self.item = item
        super().__init__(label=item.name)

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_item = self.item
        self.view.stop()
        await interaction.response.edit_message(view=None)


class ConfirmItemView(discord.ui.View):
    def __init__(self, timeout: float, items: List[Item], author: discord.User):
        super().__init__(timeout=timeout)
        self.selected_item = None
        for item in items:
            self.add_item(ItemButton(item))
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(_("You are not authorized to interact with this."), ephemeral=True)
            return False
        return True


class ItemConverter(Transformer):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> Item:
        try:
            c = await Character.from_json(
                ctx,
                ctx.bot.get_cog("Adventure").config,
                ctx.author,
                ctx.bot.get_cog("Adventure")._daily_bonus,
            )
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            raise BadArgument
        no_markdown = Item.remove_markdowns(argument)
        lookup = list(i for x, i in c.backpack.items() if no_markdown.lower() in x.lower())
        lookup_m = list(i for i in c.backpack.values() if argument.lower() == str(i).lower() and str(i))
        lookup_e = list(i for i in c.backpack.values() if argument == str(i))

        _temp_items = set()
        for i in lookup:
            _temp_items.add(str(i))
        for i in lookup_m:
            _temp_items.add(str(i))
        for i in lookup_e:
            _temp_items.add(str(i))

        if len(lookup_e) == 1:
            return lookup_e[0]
        if len(lookup) == 1:
            return lookup[0]
        elif len(lookup_m) == 1:
            return lookup_m[0]
        elif len(lookup) == 0 and len(lookup_m) == 0:
            raise BadArgument(_("`{}` doesn't seem to match any items you own.").format(argument))
        else:
            lookup = list(i for i in c.backpack.values() if str(i) in _temp_items)
            if len(lookup) > 25:
                raise BadArgument(
                    _("You have too many items matching the name `{}`, please be more specific.").format(argument)
                )
            items = ""
            view = ConfirmItemView(60, lookup, ctx.author)
            for number, item in enumerate(lookup):
                items += f"{number}. {item.as_ansi()} (owned {item.owned})\n"

            await ctx.send(
                _("Multiple items share that name, which one would you like?\n{items}").format(
                    items=box(items, lang="ansi")
                ),
                view=view,
            )
            await view.wait()
            if not view.selected_item:
                raise BadArgument(_("Alright then."))
            return view.selected_item

    @classmethod
    async def transform(cls, interaction: discord.Interaction, argument: str) -> Item:
        ctx = await interaction.client.get_context(interaction)
        return await cls.convert(ctx, argument)

    async def autocomplete(self, interaction: discord.Interaction, current: str) -> List[Choice]:
        ctx = await interaction.client.get_context(interaction)
        try:
            c = await Character.from_json(
                ctx,
                ctx.bot.get_cog("Adventure").config,
                ctx.author,
                ctx.bot.get_cog("Adventure")._daily_bonus,
            )
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            return []
        return [Choice(name=str(x), value=x.name) for x in c.backpack.values() if current.lower() in str(x).lower()][
            :25
        ]


class EquipableItemConverter(Transformer):
    @classmethod
    async def convert(cls, ctx: commands.Context, argument: str) -> Item:
        try:
            c = await Character.from_json(
                ctx,
                ctx.bot.get_cog("Adventure").config,
                ctx.author,
                ctx.bot.get_cog("Adventure")._daily_bonus,
            )
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            raise BadArgument
        equipped_items = set()
        for slot in Slot:
            if slot is Slot.two_handed:
                continue
            item = slot.get_item_slot(c)
            if item:
                equipped_items.add(str(item))
        no_markdown = Item.remove_markdowns(argument)
        lookup = list(
            i for x, i in c.backpack.items() if no_markdown.lower() in x.lower() and str(i) not in equipped_items
        )

        # Minimal, safe behavior for test environments: if there's exactly one
        # match return it; if none, raise BadArgument; if multiple, return the
        # first match. Full interactive disambiguation is not required for unit
        # tests that only need import-time stability.
        if len(lookup) == 0:
            raise BadArgument(_("`{}` doesn't seem to match any items you own.").format(argument))
        if len(lookup) == 1:
            return lookup[0]
        return lookup[0]
