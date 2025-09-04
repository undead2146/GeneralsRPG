import importlib.util
import os
import types
import pytest


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
loot_path = os.path.join(ROOT, "adventure", "loot.py")
# Ensure 'adventure' package is discoverable as a package module so relative imports
# inside files like loot.py resolve. We set a simple package module with __path__.
import sys as _sys
if "adventure" not in _sys.modules:
    pkg = types.ModuleType("adventure")
    pkg.__path__ = [os.path.join(ROOT, "adventure")]
    _sys.modules["adventure"] = pkg

import importlib
# Import the package module directly so relative imports inside the cog resolve
# (conftest.py ensures repo root is on sys.path and provides minimal stubs).
loot_mod = importlib.import_module("adventure.loot")
# Provide a minimal 'discord' stub so importing the cog module during tests doesn't
# fail at collection time when the real discord.py package isn't available.
import sys
import types as _types
if "discord" not in sys.modules:
    discord_stub = _types.ModuleType("discord")
    # minimal attributes referenced at import-time (Embed/Colour/etc. are created later)
    discord_stub.Message = type("Message", (), {})
    discord_stub.User = type("User", (), {})
    discord_stub.Embed = type("Embed", (), {})
    discord_stub.Colour = type("Colour", (), {"blurple": staticmethod(lambda: None), "dark_red": staticmethod(lambda: None), "dark_green": staticmethod(lambda: None)})
    sys.modules["discord"] = discord_stub
    # create discord.ext and discord.ext.commands stubs
    ext_mod = _types.ModuleType("discord.ext")
    commands_mod = _types.ModuleType("discord.ext.commands")
    # minimal classes used by import-time fallbacks in loot/adventure
    class Dummy:
        pass
    commands_mod.CheckFailure = Dummy
    commands_mod.Cog = Dummy
    commands_mod.hybrid_command = lambda *a, **k: (lambda f: f)
    commands_mod.cooldown = lambda *a, **k: (lambda f: f)
    commands_mod.bot_has_permissions = lambda *a, **k: (lambda f: f)
    ext_mod.commands = commands_mod
    sys.modules["discord.ext"] = ext_mod
    sys.modules["discord.ext.commands"] = commands_mod
    # stub redbot and redbot.core used by the modules
    redbot_mod = _types.ModuleType("redbot")
    redbot_core = _types.ModuleType("redbot.core")
    redbot_core.commands = commands_mod
    sys.modules["redbot"] = redbot_mod
    sys.modules["redbot.core"] = redbot_core



class DummyChar:
    def __init__(self):
        self.backpack = {}
        self.supplies_added = 0
        self.cp_added = 0
        self.added_to_backpack = []

    async def add_supplies(self, amt: int):
        self.supplies_added += int(amt)

    async def add_cp(self, amt: int):
        self.cp_added += int(amt)

    async def add_to_backpack(self, item, number: int = 1):
        self.added_to_backpack.append((getattr(item, "name", str(item)), int(number)))
        return True

    async def to_json(self, ctx=None, config=None):
        return {}


class DummyCtx:
    def __init__(self, author_id=10):
        self.author = types.SimpleNamespace(id=author_id, display_name="Tester")


class FakeEngine:
    def __init__(self, cfg, rng=None, *, rewards_map=None):
        self.cfg = cfg
        self.rng = rng
        self._map = rewards_map or {}

    def calculate(self, category, participants, _):
        return self._map


@pytest.mark.asyncio
async def test_do_work_rewardengine_applies_all_rewards(monkeypatch):
    L = loot_mod.LootCommands()
    ctx = DummyCtx(author_id=42)
    c = DummyChar()

    monkeypatch.setattr(L, "_load_theme_json", lambda name: {"gather": {}})
    rewards_map = {42: {"supplies": 5, "parts": 2, "cp": 3, "blueprints": 1}}
    monkeypatch.setattr(loot_mod, "RewardEngine", lambda cfg, rng=None: FakeEngine(cfg, rng, rewards_map=rewards_map))

    async def _noop_set(x):
        return None

    L.config = types.SimpleNamespace(user=lambda author: types.SimpleNamespace(set=_noop_set))

    ok, msg = await L.do_work(ctx, c, "gather")
    assert ok is True
    assert c.supplies_added == 5
    assert c.cp_added == 3
    names = [n for n, _ in c.added_to_backpack]
    assert any("part" in n.lower() or "parts" in n.lower() for n in names)
    assert any("blueprint" in n.lower() or "blue print" in n.lower() for n in names)


@pytest.mark.asyncio
async def test_do_work_rewardengine_fallback_on_add_supplies(monkeypatch):
    L = loot_mod.LootCommands()
    ctx = DummyCtx(author_id=99)
    c = DummyChar()

    async def bad_add_supplies(amt: int):
        raise RuntimeError("no numeric supplies")

    c.add_supplies = bad_add_supplies
    monkeypatch.setattr(L, "_load_theme_json", lambda name: {"gather": {}})
    rewards_map = {99: {"supplies": 7}}
    monkeypatch.setattr(loot_mod, "RewardEngine", lambda cfg, rng=None: FakeEngine(cfg, rng, rewards_map=rewards_map))

    async def _noop_set(x):
        return None

    L.config = types.SimpleNamespace(user=lambda author: types.SimpleNamespace(set=_noop_set))

    ok, msg = await L.do_work(ctx, c, "gather")
    assert ok is True
    assert any("supply" in n.lower() or "supplies" in n.lower() for n, _ in c.added_to_backpack)
