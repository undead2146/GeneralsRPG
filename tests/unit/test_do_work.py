import pytest

from adventure.loot import LootCommands


class DummyChar:
    def __init__(self):
        self.backpack = {}

    async def add_to_backpack(self, item, number=1):
        # emulate success unless item name contains 'fail'
        if getattr(item, "name", "").lower().find("fail") != -1:
            return False
        # record simplistic representation
        self.backpack[item.name] = self.backpack.get(item.name, 0) + number
        return True


class DummyCtx:
    def __init__(self):
        self.author = None


@pytest.mark.asyncio
async def test_do_work_gather_success(monkeypatch):
    L = LootCommands()
    ctx = DummyCtx()
    c = DummyChar()

    # monkeypatch load_theme and pick_drop
    monkeypatch.setattr(L, "_load_theme_json", lambda name: {"drops": [{"name": "wood_plank", "chance": 100, "amount": 2}]})
    monkeypatch.setattr(L, "_pick_drop", lambda drops: [("wood_plank", 2)])

    ok, msg = await L.do_work(ctx, c, "gather")
    assert ok is True
    assert "gathered" in msg.lower() or "supplies" in msg.lower()
    assert c.backpack.get("wood_plank") == 2


@pytest.mark.asyncio
async def test_do_work_salvage_failure_on_add(monkeypatch):
    L = LootCommands()
    ctx = DummyCtx()
    c = DummyChar()

    monkeypatch.setattr(L, "_load_theme_json", lambda name: {"drops": [{"name": "broken_fail_part", "chance": 100, "amount": 1}]})
    monkeypatch.setattr(L, "_pick_drop", lambda drops: [("broken_fail_part", 1)])

    ok, msg = await L.do_work(ctx, c, "salvage")
    assert ok is False
    assert "failed" in msg.lower() or "backpack" in msg.lower()


@pytest.mark.asyncio
async def test_do_work_blackmarket_risk(monkeypatch):
    L = LootCommands()
    ctx = DummyCtx()
    c = DummyChar()

    # theme says lose_chance 100 -> always lose
    monkeypatch.setattr(L, "_load_theme_json", lambda name: {"drops": [{"name": "stolen_blueprint", "chance": 100, "amount": 1}], "risk": {"lose_chance": 100}})
    monkeypatch.setattr(L, "_pick_drop", lambda drops: [("stolen_blueprint", 1)])

    ok, msg = await L.do_work(ctx, c, "blackmarket")
    assert ok is False
    assert "intercepted" in msg.lower() or "lost" in msg.lower()
