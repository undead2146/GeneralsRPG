import asyncio
import random
from types import SimpleNamespace

import pytest

from adventure.rewards import RewardEngine

# Minimal fake Character for do_work integration testing
class FakeCharacter:
    def __init__(self):
        self.backpack = {}
        self.supplies = 0
        self.cp = 0

    async def add_supplies(self, amt):
        self.supplies += int(amt)

    async def add_cp(self, amt):
        self.cp += int(amt)

    async def add_to_backpack(self, item, number=1):
        key = str(item.name)
        if key in self.backpack:
            self.backpack[key].owned += number
        else:
            # minimal Item-like object
            item.owned = number
            self.backpack[key] = item
        return True

    async def to_json(self, ctx, config):
        return {"supplies": self.supplies, "cp": self.cp, "backpack": {k: {"owned": v.owned} for k, v in self.backpack.items()}}


class FakeItem:
    def __init__(self, name):
        self.name = name
        self.owned = 0


@pytest.mark.asyncio
async def test_reward_engine_applies_rewards_deterministically(tmp_path):
    # Build a deterministic rewards config for 'gather'
    cfg = {
        "gather": {
            "supplies": [5, 5],
            "parts": [2, 2],
            "cp": [1, 1],
            "blueprints": 0.0,
        }
    }
    rng = random.Random(12345)
    engine = RewardEngine(cfg, rng=rng)
    participants = [{"id": 42}]
    rewards = engine.calculate("gather", participants, None)
    assert 42 in rewards
    r = rewards[42]
    assert r["supplies"] == 5
    assert r["parts"] == 2
    assert r["cp"] == 1


@pytest.mark.asyncio
async def test_do_work_uses_reward_engine_and_persists(monkeypatch):
    # Patch loader to return a rewards config
    from adventure.loot import LootCommands

    lc = LootCommands()

    async def fake_load(name):
        if name == "rewards":
            return {"gather": {"supplies": [3, 3], "parts": [1, 1], "cp": [0, 0], "blueprints": 0.0}}
        return None

    monkeypatch.setattr(lc, "_load_theme_json", fake_load)

    # Create fake context and character
    ctx = SimpleNamespace()
    ctx.author = SimpleNamespace(id=1)

    fake_char = FakeCharacter()

    ok, msg = await lc.do_work(ctx, fake_char, "gather")
    assert ok is True
    assert fake_char.supplies == 3
    # parts are added as backpack items named 'Parts'
    assert any("Parts" in k for k in fake_char.backpack.keys())
