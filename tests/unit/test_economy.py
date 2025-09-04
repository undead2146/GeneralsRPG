import pytest
import asyncio

from adventure.charsheet import Character


@pytest.mark.asyncio
async def test_add_supplies_and_cp_minimal():
    # create a minimal character dict via from_json pathway is complex; instantiate directly
    c = Character(
        ctx=None,
        exp=0,
        lvl=1,
        treasure=None,
        head=None,
        neck=None,
        chest=None,
        gloves=None,
        belt=None,
        legs=None,
        boots=None,
        left=None,
        right=None,
        ring=None,
        charm=None,
        backpack={},
        loadouts={},
        heroclass={},
        skill={},
        bal=0,
        user=None,
        adventures={},
        nega={},
        weekly_score={},
    )
    assert getattr(c, "supplies", 0) == 0
    assert getattr(c, "command_points", 0) == 0
    await c.add_supplies(150)
    await c.add_cp(3)
    assert c.supplies == 150
    assert c.command_points == 3


@pytest.mark.asyncio
async def test_do_work_supplies_and_cp(monkeypatch):
    # construct a LootCommands-like minimal object
    from adventure.loot import LootCommands

    class DummyCog(LootCommands):
        pass

    cog = DummyCog()

    # create a dummy context and character
    class DummyCtx:
        author = type("A", (), {"id": 1})()

    ctx = DummyCtx()

    # create a minimal character instance (reuse constructor)
    c = Character(
        ctx=ctx,
        exp=0,
        lvl=1,
        treasure=None,
        head=None,
        neck=None,
        chest=None,
        gloves=None,
        belt=None,
        legs=None,
        boots=None,
        left=None,
        right=None,
        ring=None,
        charm=None,
        backpack={},
        loadouts={},
        heroclass={},
        skill={},
        bal=0,
        user=type("U", (), {"id": 1})(),
        adventures={},
        nega={},
        weekly_score={},
    )

    # monkeypatch _load_theme_json to return a structured drops json
    async def fake_load(name):
        return {"drops": [{"name": "Supplies", "amount": [50, 50], "chance": 100}, {"name": "Command Points", "amount": [1, 1], "chance": 100}]}

    async def fake_pick(drops):
        return [("Supplies", 75), ("Command Points", 1)]

    monkeypatch.setattr(cog, "_load_theme_json", lambda name: fake_load(name))
    monkeypatch.setattr(cog, "_pick_drop", lambda drops: fake_pick(drops))

    # run do_work
    ok, msg = await cog.do_work(ctx, c, "gather")
    assert ok is True
    assert "gathered" in msg.lower() or "supplies" in msg.lower() or "added" in msg.lower()
    assert c.supplies == 75
    assert c.command_points == 1
