import pytest
from contextlib import asynccontextmanager
from types import SimpleNamespace
import importlib.util
import os

# Load the adventure/loot.py file directly to avoid importing package-level
# modules that may try to import Redbot at collection time.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
loot_path = os.path.join(ROOT, "adventure", "loot.py")
spec = importlib.util.spec_from_file_location("adventure_loot_mod", loot_path)
loot_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loot_mod)


class FakeAuthor:
    def __init__(self, display_name="Tester"):
        self.display_name = display_name


class FakeCtx:
    def __init__(self):
        self.author = FakeAuthor()
        self.sent = []

    async def send(self, content=None, **_):
        # capture sent content for assertions
        self.sent.append(content)
        return SimpleNamespace(edit=lambda **kw: None)


class FakeCharacter:
    def __init__(self, cog=None, add_success=True):
        self.cog = cog
        self.backpack = {}
        self._add_success = add_success

    @classmethod
    async def from_json(cls, ctx, config, author, daily):
        # by default tests will monkeypatch this symbol on the module
        return cls()

    async def add_to_backpack(self, item, number=1):
        return self._add_success

    async def to_json(self, ctx=None, config=None):
        return {}


def make_cog():
    # create a minimal LootCommands-like object with required attributes
    cog = object.__new__(loot_mod.LootCommands)

    async def set_dummy(x):
        return None

    cog.config = SimpleNamespace(user=lambda author: SimpleNamespace(set=set_dummy))

    async def allow_in_dm(ctx):
        return True

    cog.allow_in_dm = allow_in_dm

    @asynccontextmanager
    async def get_lock(author):
        yield None

    cog.get_lock = get_lock
    return cog


@pytest.mark.asyncio
@pytest.mark.parametrize("action,category", [("gather_action", "gather"), ("salvage_action", "salvage"), ("blackmarket_action", "blackmarket")])
async def test_action_happy(monkeypatch, action, category):
    """Happy flow: theme provides drops and add_to_backpack succeeds."""
    cog = make_cog()
    ctx = FakeCtx()

    # ensure Character.from_json returns a FakeCharacter that succeeds
    async def fake_from_json(ctx_, config, author, daily):
        return FakeCharacter(cog=cog, add_success=True)

    monkeypatch.setattr(loot_mod.Character, "from_json", fake_from_json)

    # monkeypatch cog helpers to be deterministic
    async def load_theme(name):
        # simple deterministic drop table
        return {"drops": [{"name": "Supplies", "chance": 100, "amount": [2, 2]}], "risk": {"lose_chance": 0}}

    async def pick_drop(drops):
        return [("Supplies", 2)]

    monkeypatch.setattr(cog, "_load_theme_json", load_theme)
    monkeypatch.setattr(cog, "_pick_drop", pick_drop)

    # run the requested action
    coro = getattr(cog, action)
    await coro(ctx)

    # we expect smart_embed or ctx.send to have been called with a success-related message
    assert ctx.sent, "Expected a message to be sent on successful action"
    sent_text = " ".join(str(s).lower() for s in ctx.sent if s)
    assert "gather" in sent_text or "salvage" in sent_text or "black market" in sent_text or "suppl" in sent_text


@pytest.mark.asyncio
@pytest.mark.parametrize("action,category", [("gather_action", "gather"), ("salvage_action", "salvage"), ("blackmarket_action", "blackmarket")])
async def test_action_add_to_backpack_failure(monkeypatch, action, category):
    """Failure flow: theme provides drops but add_to_backpack fails (e.g., full backpack)."""
    cog = make_cog()
    ctx = FakeCtx()

    # Character.from_json returns a FakeCharacter that fails to add items
    async def fake_from_json(ctx_, config, author, daily):
        return FakeCharacter(cog=cog, add_success=False)

    monkeypatch.setattr(loot_mod.Character, "from_json", fake_from_json)

    async def load_theme(name):
        return {"drops": [{"name": "SomePart", "chance": 100, "amount": [1, 1]}], "risk": {"lose_chance": 0}}

    async def pick_drop(drops):
        return [("SomePart", 1)]

    monkeypatch.setattr(cog, "_load_theme_json", load_theme)
    monkeypatch.setattr(cog, "_pick_drop", pick_drop)

    coro = getattr(cog, action)
    await coro(ctx)

    # Expect a failure message to be sent
    assert ctx.sent, "Expected a message to be sent on failure"
    sent_text = " ".join(str(s).lower() for s in ctx.sent if s)
    assert "backpack" in sent_text or "failed" in sent_text or "nothing" in sent_text or "lost" in sent_text
