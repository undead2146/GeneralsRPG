import pytest

from adventure.charsheet import Item
from adventure.loot import craft_from_blueprint


class DummyCtx:
    pass


class DummyCharacter:
    def __init__(self, backpack=None, cog=None):
        self.backpack = backpack or {}
        # attach a minimal cog-like object if needed
        self.cog = cog

    async def add_to_backpack(self, item: Item, number: int = 1):
        # default behaviour: add and return True
        if item.name in self.backpack:
            self.backpack[item.name].owned += number
        else:
            self.backpack[item.name] = item
        return True


@pytest.mark.asyncio
async def test_recipe_loaded_from_json_and_crafted(tmp_path):
    # prepare a theme recipes.json in a temp folder and a minimal cog _load_theme_json helper
    recipes = {"mech": {"parts": 2, "supplies": 10, "product": "Mech"}}

    class CogLike:
        async def _load_theme_json(self, name: str):
            if name == "recipes":
                return recipes
            return None

    c = DummyCharacter()
    c.cog = CogLike()
    ctx = DummyCtx()
    # add blueprint and required resources
    bp = Item(ctx=ctx, name="Mech Blueprint", slot=["chest"], rarity="event", owned=1)
    c.backpack[bp.name] = bp
    parts = Item(ctx=ctx, name="Scrap Part", slot=["chest"], rarity="normal", owned=2, parts=1)
    c.backpack[parts.name] = parts
    supplies = Item(ctx=ctx, name="Supplies", slot=["chest"], rarity="normal", owned=20)
    c.backpack[supplies.name] = supplies

    success, msg = await craft_from_blueprint(ctx, c, "mech")
    assert success is True
    assert any(name.lower().startswith("mech") for name in c.backpack.keys())


@pytest.mark.asyncio
async def test_insufficient_parts_blocks_build():
    class CogLike:
        async def _load_theme_json(self, name: str):
            return {"mech": {"parts": 5, "supplies": 10, "product": "Mech"}} if name == "recipes" else None

    c = DummyCharacter()
    c.cog = CogLike()
    ctx = DummyCtx()
    bp = Item(ctx=ctx, name="Mech Blueprint", slot=["chest"], rarity="event", owned=1)
    c.backpack[bp.name] = bp
    # only 1 part available but 5 required
    part = Item(ctx=ctx, name="Scrap Part", slot=["chest"], rarity="normal", owned=1, parts=1)
    c.backpack[part.name] = part
    supplies = Item(ctx=ctx, name="Supplies", slot=["chest"], rarity="normal", owned=50)
    c.backpack[supplies.name] = supplies

    success, msg = await craft_from_blueprint(ctx, c, "mech")
    assert success is False
    assert "parts" in msg.lower()


@pytest.mark.asyncio
async def test_add_to_backpack_failure_rolls_back_consumption():
    # simulate add_to_backpack raising/returning False
    class CogLike:
        async def _load_theme_json(self, name: str):
            return {"mech": {"parts": 1, "supplies": 5, "product": "Mech"}} if name == "recipes" else None

    class BrokenCharacter(DummyCharacter):
        async def add_to_backpack(self, item: Item, number: int = 1):
            return False

    c = BrokenCharacter()
    c.cog = CogLike()
    ctx = DummyCtx()
    bp = Item(ctx=ctx, name="Mech Blueprint", slot=["chest"], rarity="event", owned=1)
    c.backpack[bp.name] = bp
    part = Item(ctx=ctx, name="Scrap Part", slot=["chest"], rarity="normal", owned=1, parts=1)
    c.backpack[part.name] = part
    supplies = Item(ctx=ctx, name="Supplies", slot=["chest"], rarity="normal", owned=10)
    c.backpack[supplies.name] = supplies

    success, msg = await craft_from_blueprint(ctx, c, "mech")
    assert success is False
    # resources should be restored (part and supplies still present)
    assert any('scrap' in name.lower() for name in c.backpack.keys())
    assert any('supply' in name.lower() for name in c.backpack.keys())
