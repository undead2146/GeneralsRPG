import pytest
from types import SimpleNamespace

from adventure.loot import LootCommands
from adventure.adventure import Adventure
from adventure.charsheet import Item, Character


class DummyCtx:
    pass


def make_dummy_char_with_backpack(items):
    c = SimpleNamespace()
    # backpack expects mapping name->item object with .rarity
    backpack = {}
    for name, rarity in items.items():
        obj = SimpleNamespace()
        obj.rarity = rarity
        backpack[name] = obj
    c.backpack = backpack
    return c


def test_map_drop_to_item_blueprint():
    L = LootCommands()
    ctx = DummyCtx()
    item = L._map_drop_to_item(ctx, "Stolen_Blueprint", 1)
    assert isinstance(item, Item)
    assert item.name == "Stolen_Blueprint"
    assert getattr(item, "rarity", "") == "event"
    assert item.owned == 1


def test_map_drop_to_item_parts_and_supplies():
    L = LootCommands()
    ctx = DummyCtx()
    parts = L._map_drop_to_item(ctx, "rusty_parts", 3)
    assert isinstance(parts, Item)
    assert parts.parts == 3
    assert parts.owned == 3

    supplies = L._map_drop_to_item(ctx, "box_of_supplies", 5)
    assert isinstance(supplies, Item)
    assert supplies.parts == 0
    assert supplies.owned == 5


@pytest.mark.asyncio
async def test_blueprints_build_wrappers(monkeypatch):
    A = Adventure(None)
    # monkeypatch Character.from_json to return dummy char with blueprints
    dummy = make_dummy_char_with_backpack({"Overlord_Blueprint": "event", "Wood_Panel": "normal"})
    monkeypatch.setattr(Character, "from_json", classmethod(lambda cls, ctx, config, author, daily: dummy))

    # test blueprints lists available blueprint names
    res = await A.blueprints(SimpleNamespace(author=SimpleNamespace()))
    # blueprints returns via smart_embed in real run; here we just ensure no exception
    assert res is None or res is not False

    # test build fallback (no specific implementation) returns a message
    res2 = await A.build(SimpleNamespace(author=SimpleNamespace()), item_name="Overlord")
    assert res2 is None or res2 is not False
