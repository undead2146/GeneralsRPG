import asyncio

from adventure.core.items import Item, craft_from_blueprint


class DummyChar:
    def __init__(self):
        self.backpack = {}


def test_craft_no_blueprint():
    c = DummyChar()
    ok, msg = asyncio.get_event_loop().run_until_complete(craft_from_blueprint(None, c, "NonExistent"))
    assert ok is False
    assert "No blueprint" in msg


def test_craft_not_enough_parts():
    c = DummyChar()
    # add a blueprint entry but not enough parts
    c.backpack["Widget Blueprint"] = Item("Widget Blueprint", "event", owned=1)
    c.backpack["Parts"] = 1
    ok, msg = asyncio.get_event_loop().run_until_complete(craft_from_blueprint(None, c, "Widget Blueprint"))
    assert ok is False
    assert "Not enough Parts" in msg
