import os
import sys
import types
from pathlib import Path
import asyncio
import inspect
import pytest

# Normalize preexisting redbot entries: if a non-package module named 'redbot'
# or 'redbot.core' exists in sys.modules (for example, left over from other
# tooling), replace it with a package-like module so importlib can import
# submodules such as 'redbot.core.i18n'. This is safe for the test shim path
# because the testing environment doesn't provide the real Red runtime.
def _normalize_redbot_entries():
    rb = sys.modules.get("redbot")
    if rb is None or not getattr(rb, "__path__", None):
        m = types.ModuleType("redbot")
        m.__path__ = []
        sys.modules["redbot"] = m
    rc = sys.modules.get("redbot.core")
    if rc is None or not getattr(rc, "__path__", None):
        m2 = types.ModuleType("redbot.core")
        m2.__path__ = []
        sys.modules["redbot.core"] = m2


_normalize_redbot_entries()

# Early shims: ensure group-like decorators and vendored menus exist before any
# package imports. This prevents import-time decorators in class bodies from
# failing when a stubbed `commands.group` returns a plain function.
try:
    # Provide a group-like shim
    class _GroupShimEarly:
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

    def _group_early(*a, **k):
        def _decor(f):
            return _GroupShimEarly(f)

        return _decor

    if "redbot.core.commands" in sys.modules:
        sys.modules["redbot.core.commands"].group = _group_early
        sys.modules["redbot.core.commands"].hybrid_group = _group_early
    else:
        # create minimal module so later imports find group/hybrid_group
        core_cmds = types.ModuleType("redbot.core.commands")
        core_cmds.group = _group_early
        core_cmds.hybrid_group = _group_early
        core_cmds.Cog = type("Cog", (), {})
        sys.modules["redbot.core.commands"] = core_cmds

    # Ensure vendored menus path exists
    if "redbot.vendored.discord.ext.menus" not in sys.modules:
        menus_mod = types.ModuleType("redbot.vendored.discord.ext.menus")
        class _PageSource: pass
        class _MenuPages: pass
        menus_mod.ListPageSource = _PageSource
        menus_mod.MenuPages = _MenuPages
        if "redbot.vendored" not in sys.modules:
            sys.modules["redbot.vendored"] = types.ModuleType("redbot.vendored")
        if "redbot.vendored.discord" not in sys.modules:
            sys.modules["redbot.vendored.discord"] = types.ModuleType("redbot.vendored.discord")
        if "redbot.vendored.discord.ext" not in sys.modules:
            sys.modules["redbot.vendored.discord.ext"] = types.ModuleType("redbot.vendored.discord.ext")
        sys.modules["redbot.vendored.discord.ext.menus"] = menus_mod
except Exception:
    pass

# Ensure repo root is on sys.path so local packages are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _install_test_stubs():
    """Install lightweight runtime stubs for third-party packages used by
    the adventure package so pytest can import modules without having
    the full discord/redbot stack installed.
    """
    # discord base
    if "discord" not in sys.modules:
        discord = types.ModuleType("discord")
        discord.Message = type("Message", (), {})
        discord.User = type("User", (), {})
        discord.Embed = type("Embed", (), {})
        discord.Colour = type(
            "Colour",
            (),
            {
                "blurple": staticmethod(lambda: None),
                "dark_green": staticmethod(lambda: None),
                "dark_red": staticmethod(lambda: None),
                "from_str": staticmethod(lambda s: None),
            },
        )
        # Minimal channel types used by some type annotations
        discord.TextChannel = type("TextChannel", (), {})
        # Minimal Member type used in type annotations
        discord.Member = type("Member", (), {})
        # Minimal Interaction type used by command views/menus
        class _Response:
            async def edit_message(self, *a, **k):
                return None

            async def send(self, *a, **k):
                return None

        class Interaction:
            def __init__(self, *a, **k):
                # provide a `.response` object with async helpers used in code
                self.response = _Response()

        discord.Interaction = Interaction
        # utils and ui submodules used by adventure.helpers
        discord.utils = types.ModuleType("discord.utils")
        discord.utils.MISSING = object()
        discord.ui = types.ModuleType("discord.ui")
        class _View:
            def __init__(self, timeout=None):
                self.timeout = timeout
                self._items = []

            def add_item(self, item):
                # attach view to item for callbacks
                try:
                    item.view = self
                except Exception:
                    pass
                self._items.append(item)

            def stop(self):
                pass

        class _Modal:
            def __init__(self, *a, **k):
                self._items = []

            def add_item(self, item):
                try:
                    item.view = self
                except Exception:
                    pass
                self._items.append(item)

        discord.ui.Modal = _Modal

        class _Button:
            def __init__(self, *a, **k):
                self.view = None

            async def callback(self, interaction):
                return None

        discord.ui.Button = _Button
        discord.ui.View = _View

        def _button(*a, **k):
            def _decor(fn):
                return fn

            return _decor

        discord.ui.button = _button

        class _ButtonStyle:
            @staticmethod
            def green():
                return 1

            @staticmethod
            def red():
                return 2

            @staticmethod
            def blurple():
                return 3

            @staticmethod
            def grey():
                return 4

        discord.ButtonStyle = _ButtonStyle

        # Select API used by adventure.ui.cart.TraderSelect
        class _Select:
            def __init__(self, *, min_values=1, max_values=1, placeholder=None, options=None):
                self.min_values = min_values
                self.max_values = max_values
                self.placeholder = placeholder
                self.options = options or []
                self.values = []
                self.view = None

            async def callback(self, interaction):
                return None

        class _SelectOption:
            def __init__(self, label=None, value=None, description=None, emoji=None):
                self.label = label
                self.value = value
                self.description = description
                self.emoji = emoji

        discord.ui.Select = _Select
        discord.SelectOption = _SelectOption

        # Text input and text style used by TraderModal
        class _TextInput:
            def __init__(self, label=None, style=None, placeholder=None, max_length=None, min_length=None, required=True):
                self.label = label
                self.style = style
                self.placeholder = placeholder
                self.max_length = max_length
                self.min_length = min_length
                self.required = required
                self.value = ""

        class _TextStyle:
            short = 1

        discord.ui.TextInput = _TextInput
        discord.TextStyle = _TextStyle
        sys.modules["discord"] = discord
        sys.modules["discord.utils"] = discord.utils
        sys.modules["discord.ui"] = discord.ui

    # discord.ext.commands minimal
    if "discord.ext.commands" not in sys.modules:
        ext = types.ModuleType("discord.ext")
        commands_mod = types.ModuleType("discord.ext.commands")
        commands_mod.Cog = type("Cog", (), {})
        commands_mod.CheckFailure = type("CheckFailure", (), {})
        commands_mod.hybrid_command = lambda *a, **k: (lambda f: f)
        commands_mod.cooldown = lambda *a, **k: (lambda f: f)
        commands_mod.bot_has_permissions = lambda *a, **k: (lambda f: f)
        commands_mod.guild_only = lambda *a, **k: (lambda f: f)
        commands_mod.check = lambda *a, **k: (lambda f: f)
        ext.commands = commands_mod
        sys.modules["discord.ext"] = ext
        sys.modules["discord.ext.commands"] = commands_mod

    # converter / errors submodules used by adventure.converters
    if "discord.ext.commands.converter" not in sys.modules:
        conv_mod = types.ModuleType("discord.ext.commands.converter")
        class Converter:
            pass
        conv_mod.Converter = Converter
        sys.modules["discord.ext.commands.converter"] = conv_mod

    if "discord.ext.commands.errors" not in sys.modules:
        errors_mod = types.ModuleType("discord.ext.commands.errors")
        class BadArgument(Exception):
            pass
        errors_mod.BadArgument = BadArgument
        sys.modules["discord.ext.commands.errors"] = errors_mod

    # app_commands shim
    if "discord.app_commands" not in sys.modules:
        app_cmds = types.ModuleType("discord.app_commands")
        class Choice:
            def __init__(self, name, value):
                self.name = name
                self.value = value
        class Transformer:
            pass
        app_cmds.Choice = Choice
        app_cmds.Transformer = Transformer
        # Minimal rename decorator used in annotations like
        # @discord.app_commands.rename(clz="class")
        def _rename(**kwargs):
            def _decor(func):
                return func

            return _decor

        app_cmds.rename = _rename
        # Also attach to the top-level discord module so attribute access
        # like `discord.app_commands.Choice` succeeds during imports.
        try:
            discord.app_commands = app_cmds
        except Exception:
            pass
        sys.modules["discord.app_commands"] = app_cmds

    # redbot base stub
    if "redbot" not in sys.modules:
        redbot = types.ModuleType("redbot")
        # Make the fake module package-like so importlib can resolve
        # submodules like redbot.core and redbot.core.i18n.
        redbot.__path__ = []
        class VersionInfo:
            def __init__(self, major=0, minor=0, patch=0):
                self.major = major
                self.minor = minor
                self.patch = patch
            @classmethod
            def from_str(cls, s: str):
                parts = [int(p) for p in s.split(".")]
                while len(parts) < 3:
                    parts.append(0)
                return cls(*parts[:3])
            def __ge__(self, other):
                return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
        redbot.version_info = VersionInfo.from_str("3.4.0")
        sys.modules["redbot"] = redbot

    # redbot.core and useful submodules
    if "redbot.core" not in sys.modules:
        core = types.ModuleType("redbot.core")
        # mark as package so imports like 'redbot.core.i18n' are allowed
        core.__path__ = []
        # commands shim
        commands_mod = types.ModuleType("redbot.core.commands")
        commands_mod.Cog = type("Cog", (), {})
        commands_mod.Context = type("Context", (), {})
        # FlagConverter used in adventure.converters
        class FlagConverter:
            def __init__(self, *a, **k):
                pass

            def __init_subclass__(cls, **kwargs):
                # Accept keyword args like case_insensitive=True used by
                # redbot.core.commands.FlagConverter subclasses in the project.
                return super().__init_subclass__(**{})

        class Converter:
            pass

        commands_mod.Converter = Converter
        # Provide a 'commands' attribute for 'from redbot.core.commands import commands'
        commands_mod.commands = commands_mod
        commands_mod.FlagConverter = FlagConverter

        # Greedy shim used in parameter annotations like commands.Greedy[discord.User]
        class Greedy(list):
            @classmethod
            def __class_getitem__(cls, item):
                return cls

        commands_mod.Greedy = Greedy

        def flag(*a, **k):
            def _inner(default=None, **kw):
                return default

            return _inner

        commands_mod.flag = flag
        commands_mod.check = lambda *a, **k: (lambda f: f)
        commands_mod.hybrid_command = lambda *a, **k: (lambda f: f)
        commands_mod.cooldown = lambda *a, **k: (lambda f: f)
        commands_mod.bot_has_permissions = lambda *a, **k: (lambda f: f)
        # is_owner is used frequently in developer-only commands
        commands_mod.is_owner = lambda *a, **k: (lambda f: f)
        # BucketType shim for cooldown decorators
        class BucketType:
            guild = 1
            user = 2
            default = 0

        commands_mod.BucketType = BucketType
        # common Red decorator shims used throughout the adventure package
        commands_mod.admin_or_permissions = lambda *a, **k: (lambda f: f)
        commands_mod.is_owner = lambda *a, **k: (lambda f: f)
        commands_mod.UserFeedbackCheckFailure = type("UserFeedbackCheckFailure", (Exception,), {})
        # Provide group decorator used by AdventureSetCommands. Return a
        # Group-like object so decorated subcommands can use `.command()`
        # in tests without the full Red runtime.
        class _GroupShim:
            def __init__(self, func):
                self._func = func

            def command(self, *a, **k):
                def _decorator(f):
                    return f

                return _decorator

            def group(self, *a, **k):
                return self.command(*a, **k)

            def __call__(self, *a, **k):
                return self._func(*a, **k)

        def _group(*a, **k):
            # supports both @commands.group and @commands.group()
            def _decorator(f):
                return _GroupShim(f)

            return _decorator

        commands_mod.group = _group
        commands_mod.hybrid_group = _group
        commands_mod.guild_only = lambda *a, **k: (lambda f: f)
        core.commands = commands_mod

        # Provide a minimal redbot.vendored.discord.ext.menus stub so code
        # importing that path doesn't fail during test collection.
        if "redbot.vendored" not in sys.modules:
                vendored = types.ModuleType("redbot.vendored")
                sys.modules["redbot.vendored"] = vendored

                discord_ext = types.ModuleType("redbot.vendored.discord.ext")
                menus_mod_v = types.ModuleType("redbot.vendored.discord.ext.menus")

                def start_adding_reactions(msg, emojis):
                    return None

                # Provide ListPageSource and MenuPages used by adventure.menus
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

                menus_mod_v.start_adding_reactions = start_adding_reactions
                menus_mod_v.ListPageSource = _PageSource
                menus_mod_v.MenuPages = _MenuPages

                sys.modules["redbot.vendored.discord.ext"] = discord_ext
                setattr(discord_ext, 'menus', menus_mod_v)
                sys.modules["redbot.vendored.discord.ext.menus"] = menus_mod_v
        # Add utility expected by adventure.adventureset
        def get_dict_converter(mapping=None, **kwargs):
            mapping = mapping or {}

            class _C:
                def __init__(self, value=None):
                    self.value = value

                def __call__(self, arg):
                    return mapping.get(arg, arg)

            return _C

        commands_mod.get_dict_converter = get_dict_converter

        # minimal Config shim
        class ConfigShim:
            @classmethod
            def get_conf(cls, *a, **k):
                return None

        core.Config = ConfigShim

        # bot shim
        bot_mod = types.ModuleType("redbot.core.bot")
        bot_mod.Red = type("Red", (), {})
        sys.modules["redbot.core.bot"] = bot_mod

        # data_manager shim
        data_manager = types.ModuleType("redbot.core.data_manager")

        def bundled_data_path(cog):
            return Path(cog.__file__).parent / "data"

        def cog_data_path(cog):
            return Path(cog.__file__).parent / "data"

        data_manager.bundled_data_path = bundled_data_path
        data_manager.cog_data_path = cog_data_path
        sys.modules["redbot.core.data_manager"] = data_manager

        # bank shim
        bank_mod = types.ModuleType("redbot.core.bank")

        async def _async_zero(*a, **k):
            return 0

        def _Account(*a, **k):
            return object()

        class BankPruneError(Exception):
            pass

        bank_mod.Account = _Account
        bank_mod.BankPruneError = BankPruneError
        bank_mod.set_balance = _async_zero
        bank_mod.get_balance = _async_zero
        bank_mod.withdraw_credits = _async_zero
        bank_mod.deposit_credits = _async_zero
        bank_mod.get_account = _async_zero
        sys.modules["redbot.core.bank"] = bank_mod
        core.bank = bank_mod

        # errors shim
        errors_mod = types.ModuleType("redbot.core.errors")

        class BalanceTooHigh(Exception):
            pass

        errors_mod.BalanceTooHigh = BalanceTooHigh
        sys.modules["redbot.core.errors"] = errors_mod

        # i18n shim
        i18n = types.ModuleType("redbot.core.i18n")
        i18n.Translator = lambda name, file: (lambda s: s)
        i18n.cog_i18n = lambda x: (lambda c: c)
        i18n.set_contextual_locales_from_guild = lambda *a, **k: None
        sys.modules["redbot.core.i18n"] = i18n

        # utils shims
        utils = types.ModuleType("redbot.core.utils")
        utils.AsyncIter = type("AsyncIter", (), {})
        chat_fmt = types.ModuleType("redbot.core.utils.chat_formatting")
        chat_fmt.bold = lambda x: str(x)
        chat_fmt.box = lambda x, lang=None: str(x)
        chat_fmt.humanize_list = lambda x: ", ".join(x) if isinstance(x, (list, tuple)) else str(x)
        chat_fmt.humanize_number = lambda x: str(x)
        chat_fmt.pagify = lambda x, page_length=1900: [x]
        chat_fmt.escape = lambda x, formatting=False: str(x)
        sys.modules["redbot.core.utils"] = utils
        sys.modules["redbot.core.utils.chat_formatting"] = chat_fmt

        # common_filters used by adventure.helpers
        common_filters_mod = types.ModuleType("redbot.core.utils.common_filters")

        def filter_various_mentions(text: str) -> str:
            return text

        common_filters_mod.filter_various_mentions = filter_various_mentions
        sys.modules["redbot.core.utils.common_filters"] = common_filters_mod

        preds = types.ModuleType("redbot.core.utils.predicates")
        preds.ReactionPredicate = type("ReactionPredicate", (), {"NUMBER_EMOJIS": []})
        sys.modules["redbot.core.utils.predicates"] = preds

        # menus helper used by converters
        menus_mod = types.ModuleType("redbot.core.utils.menus")

        def start_adding_reactions(msg, emojis):
            return None

        menus_mod.start_adding_reactions = start_adding_reactions
        sys.modules["redbot.core.utils.menus"] = menus_mod

        sys.modules["redbot.core.commands"] = commands_mod
        sys.modules["redbot.core"] = core

    # lightweight adventure.charsheet stub to avoid importing heavy module at collection
    if "adventure.charsheet" not in sys.modules:
        chs = types.ModuleType("adventure.charsheet")
        class _Item:
            def __init__(self, **kwargs):
                self.name = kwargs.get("name", "item")
                self.owned = kwargs.get("owned", 1)
                self.parts = kwargs.get("parts", 0)
                self.rarity = kwargs.get("rarity", "normal")
            def to_json(self):
                return {self.name: {}}
            def __str__(self):
                return self.name
        class _Character:
            def __init__(self, **kwargs):
                self.backpack = kwargs.get("backpack", {})
            @classmethod
            async def from_json(cls, ctx, config, user, daily):
                return cls(backpack={})
        chs.Item = _Item
        chs.Character = _Character
        async def calculate_sp(lvl_end: int, c=None):
            # Minimal placeholder used during tests; real logic lives in
            # the production module. Return 0 to keep behaviour deterministic.
            return 0

        async def has_funds(user, cost):
            # Tests that need realistic behaviour should mock bank.can_spend.
            return True

        chs.calculate_sp = calculate_sp
        chs.has_funds = has_funds
        sys.modules["adventure.charsheet"] = chs


_install_test_stubs()

# Final verification: ensure both commands.group and commands.hybrid_group
# return a Group-like object exposing .command()/.group(). If some other code
# replaced the shim earlier in the import chain, overwrite both with a robust
# version so decorated subcommands can attach at import time in tests.
try:
    cmds_mod = sys.modules.get("redbot.core.commands")
    if cmds_mod is not None:
        def _is_group_like(dec):
            try:
                maybe = dec()(lambda: None)
                return hasattr(maybe, "command")
            except Exception:
                return False

        need_fix = False
        for name in ("group", "hybrid_group"):
            dec = getattr(cmds_mod, name, None)
            if callable(dec):
                if not _is_group_like(dec):
                    need_fix = True
                    break
            else:
                need_fix = True
                break

        if need_fix:
            # Replace with robust shim for both group and hybrid_group
            class _GroupShimFinal:
                def __init__(self, func):
                    self._func = func

                def command(self, *a, **k):
                    def _decorator(f):
                        return f

                    return _decorator

                def group(self, *a, **k):
                    return self.command(*a, **k)

                def __call__(self, *a, **k):
                    return self._func(*a, **k)

            def _group_final(*a, **k):
                def _decor(f):
                    return _GroupShimFinal(f)

                return _decor

            setattr(cmds_mod, "group", _group_final)
            setattr(cmds_mod, "hybrid_group", _group_final)
except Exception:
    pass


# If pytest-asyncio isn't installed, run coroutine test functions ourselves so
# tests using @pytest.mark.asyncio still execute. This keeps CI/local runs
# working without adding an external dependency.
@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    testfunc = pyfuncitem.obj
    if inspect.iscoroutinefunction(testfunc):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(testfunc(**pyfuncitem.funcargs))
            return True
        finally:
            loop.close()
    return None
