import os
import sys
import asyncio
import types
import pytest

# Ensure the repository root is on sys.path so local packages (redbot stub, adventure) are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from types import SimpleNamespace

import adventure.loot as lootmod


class DummyCtx:
    def __init__(self):
        self.author = SimpleNamespace(id=1, display_name="Tester")
        self.guild = None


class DummyCharacter:
    def __init__(self):
        self.backpack = {}

    async def add_to_backpack(self, item, number=1):
        # simulate storing Item instances
        if item.name in self.backpack:
            self.backpack[item.name].owned += number
        else:
            self.backpack[item.name] = item

    async def to_json(self, ctx, config):
        return {}


class DummyLoot(lootmod.LootCommands):
    def __init__(self):
        # don't call parent init
        pass


@pytest.mark.asyncio
async def test_gather_success(monkeypatch, tmp_path):
    ctx = DummyCtx()
    L = DummyLoot()

    # monkeypatch config/theme loaders to return a deterministic gather table
    async def fake_load(name):
        return {"drops": [{"name": "metal_scrap", "chance": 100, "amount": [1, 2]}]}

    monkeypatch.setattr(L, "_load_theme_json", lambda name: fake_load(name))

    # mock Character.from_json to return DummyCharacter
    async def fake_from_json(ctx_arg, config, user, daily):
        return DummyCharacter()

    monkeypatch.setattr(lootmod.Character, "from_json", staticmethod(fake_from_json))

    # control pick to return specific value
    monkeypatch.setattr(L, "_pick_drop", lambda drops: [("metal_scrap", 2)])

    # run gather_action
    await L.gather_action(ctx)

    # verify no exception and mapping produced an Item (implicit)


@pytest.mark.asyncio
async def test_salvage_success(monkeypatch):
    ctx = DummyCtx()
    L = DummyLoot()

    async def fake_load(name):
        return {"drops": [{"name": "vehicle_part", "chance": 100, "amount": 1}]}

    monkeypatch.setattr(L, "_load_theme_json", lambda name: fake_load(name))

    async def fake_from_json(ctx_arg, config, user, daily):
        return DummyCharacter()

    monkeypatch.setattr(lootmod.Character, "from_json", staticmethod(fake_from_json))
    monkeypatch.setattr(L, "_pick_drop", lambda drops: [("vehicle_part", 1)])

    await L.salvage_action(ctx)


@pytest.mark.asyncio
async def test_blackmarket_loss(monkeypatch):
    ctx = DummyCtx()
    L = DummyLoot()

    async def fake_load(name):
        return {"drops": [{"name": "stolen_blueprint", "chance": 100, "amount": 1}], "risk": {"lose_chance": 100}}

    monkeypatch.setattr(L, "_load_theme_json", lambda name: fake_load(name))

    async def fake_from_json(ctx_arg, config, user, daily):
        return DummyCharacter()

    monkeypatch.setattr(lootmod.Character, "from_json", staticmethod(fake_from_json))

    # Force pick to return something
    monkeypatch.setattr(L, "_pick_drop", lambda drops: [("stolen_blueprint", 1)])

    # Run blackmarket_action and expect it to return early due to loss (lose_chance 100)
    await L.blackmarket_action(ctx)
