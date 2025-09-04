import asyncio
import pytest

from adventure.charsheet import Character, Item
from adventure.loot import craft_from_blueprint


class DummyCtx:
    pass


class DummyCharacter:
    def __init__(self):
        self.backpack = {}

    async def add_to_backpack(self, item: Item, number: int = 1):
        if item.name in self.backpack:
            self.backpack[item.name].owned += number
        else:
            self.backpack[item.name] = item


@pytest.mark.asyncio
async def test_craft_consumes_blueprint_and_creates_item():
    ctx = DummyCtx()
    c = DummyCharacter()
    # create a blueprint item for a non-recipe product (no parts required)
    bp = Item(ctx=ctx, name="Garrison Blueprint", slot=["chest"], rarity="event", owned=1)
    c.backpack[bp.name] = bp

    success, msg = await craft_from_blueprint(ctx, c, "garrison")
    assert success is True
    # blueprint should be consumed
    assert all("Blueprint" not in name for name in c.backpack.keys())
    # crafted item present
    assert any(name.lower().startswith("garrison") for name in c.backpack.keys())


@pytest.mark.asyncio
async def test_craft_requires_and_consumes_parts_and_supplies():
    ctx = DummyCtx()
    c = DummyCharacter()
    # blueprint
    bp = Item(ctx=ctx, name="Tank Blueprint", slot=["chest"], rarity="event", owned=1)
    c.backpack[bp.name] = bp
    # add parts: part items will have parts=1 and owned count
    part_item = Item(ctx=ctx, name="Scrap Part", slot=["chest"], rarity="normal", owned=5, parts=1)
    c.backpack[part_item.name] = part_item
    # add supplies item
    supplies = Item(ctx=ctx, name="Supplies", slot=["chest"], rarity="normal", owned=200)
    c.backpack[supplies.name] = supplies

    success, msg = await craft_from_blueprint(ctx, c, "tank")
    assert success is True
    # blueprint consumed
    assert all("Blueprint" not in name for name in c.backpack.keys())
    # parts consumed (should be less than initial 5)
    remaining_parts = sum(getattr(i, 'owned', 0) for i in c.backpack.values() if 'part' in i.name.lower())
    assert remaining_parts < 5
    # supplies consumed
    remaining_supplies = sum(getattr(i, 'owned', 0) for i in c.backpack.values() if 'supply' in i.name.lower())
    assert remaining_supplies < 200
