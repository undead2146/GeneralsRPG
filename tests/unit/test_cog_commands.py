import asyncio
import time
import pytest
from types import SimpleNamespace

import adventure.units as unitsmod
from adventure.charsheet import Character
from adventure.adventure import Adventure


class FakeChar:
    def __init__(self, units_serialized):
        # simple backing attrs expected by the cog
        self.backpack = {}
        self.supplies = 0
        self.repair_kits = 0
        self.units = units_serialized

    async def to_json(self, ctx, config):
        # return minimal serializable form expected by persistence
        return {"supplies": self.supplies, "repair_kits": self.repair_kits, "units": self.units, "backpack": {k: {"owned": v.owned} for k, v in self.backpack.items()}}


class DummyCtx:
    def __init__(self):
        self.author = SimpleNamespace(id=1, display_name="Tester")
        self.guild = None
        self.message = None


@pytest.mark.asyncio
async def test_heal_command_persists_and_consumes_supplies(monkeypatch):
    A = Adventure(None)
    # create a unit with hp < max
    u = unitsmod.UnitState(id_="u1", type_="Infantry", hp=20, max_hp=100, status="active")
    units_ser = unitsmod.units_to_serialized({u.id: u})
    fake = FakeChar(units_ser)
    fake.supplies = 100

    async def fake_from_json(ctx, config, author, daily):
        return fake

    monkeypatch.setattr(Character, "from_json", staticmethod(fake_from_json))

    persisted = []

    # mock config.user(...).set
    A.config = SimpleNamespace(user=lambda author: SimpleNamespace(set=(lambda x: persisted.append(x) or asyncio.sleep(0))))

    ctx = DummyCtx()
    # call heal command
    await A.heal_unit_cmd(ctx, "u1", amount=30)
    # ensure persistence was attempted
    assert persisted, "heal did not persist character"
    last = persisted[-1]
    assert last.get("supplies", None) == 70


@pytest.mark.asyncio
async def test_repair_command_with_kit_and_parts(monkeypatch):
    A = Adventure(None)
    # downed unit
    u = unitsmod.UnitState(id_="u2", type_="Vehicle", hp=0, max_hp=200, status="downed")
    units_ser = unitsmod.units_to_serialized({u.id: u})

    # test kit
    fake1 = FakeChar(units_ser)
    fake1.repair_kits = 1

    async def fake_from_json_kit(ctx, config, author, daily):
        return fake1

    monkeypatch.setattr(Character, "from_json", staticmethod(fake_from_json_kit))

    persisted_kit = []
    A.config = SimpleNamespace(user=lambda author: SimpleNamespace(set=(lambda x: persisted_kit.append(x) or asyncio.sleep(0))))

    ctx = DummyCtx()
    await A.repair_unit_cmd(ctx, "u2", mode="kit")
    assert persisted_kit, "repair (kit) did not persist"
    last = persisted_kit[-1]
    assert last.get("repair_kits", None) == 0
    # ensure units serialized shows active unit
    units_after = unitsmod.units_from_serialized(last.get("units"))
    assert units_after["u2"].status == "active"
    assert units_after["u2"].hp >= int(0.4 * units_after["u2"].max_hp)

    # test parts
    u2 = unitsmod.UnitState(id_="u3", type_="Vehicle", hp=0, max_hp=200, status="downed")
    units_ser2 = unitsmod.units_to_serialized({u2.id: u2})
    fake2 = FakeChar(units_ser2)
    class Item:
        def __init__(self, owned):
            self.owned = owned
    fake2.backpack = {"Parts": Item(3)}

    async def fake_from_json_parts(ctx, config, author, daily):
        return fake2

    monkeypatch.setattr(Character, "from_json", staticmethod(fake_from_json_parts))

    persisted_parts = []
    A.config = SimpleNamespace(user=lambda author: SimpleNamespace(set=(lambda x: persisted_parts.append(x) or asyncio.sleep(0))))

    await A.repair_unit_cmd(ctx, "u3", mode="parts")
    assert persisted_parts, "repair (parts) did not persist"
    last = persisted_parts[-1]
    units_after = unitsmod.units_from_serialized(last.get("units"))
    assert units_after["u3"].status == "active"
    assert units_after["u3"].hp >= int(0.25 * units_after["u3"].max_hp)


@pytest.mark.asyncio
async def test_recover_command_persists_passive_recover(monkeypatch):
    A = Adventure(None)
    # unit with past tick
    now = int(time.time())
    u = unitsmod.UnitState(id_="u4", type_="Infantry", hp=50, max_hp=100, status="active")
    u.next_tick_at = now - 10
    units_ser = unitsmod.units_to_serialized({u.id: u})
    fake = FakeChar(units_ser)

    async def fake_from_json(ctx, config, author, daily):
        return fake

    monkeypatch.setattr(Character, "from_json", staticmethod(fake_from_json))

    persisted = []
    A.config = SimpleNamespace(user=lambda author: SimpleNamespace(set=(lambda x: persisted.append(x) or asyncio.sleep(0))))

    ctx = DummyCtx()
    await A.recover_units_cmd(ctx)
    assert persisted, "recover did not persist"
    last = persisted[-1]
    units_after = unitsmod.units_from_serialized(last.get("units"))
    assert units_after["u4"].hp > 50


def test_cooldown_decorators_present():
    # Ensure the command functions have cooldown decorators in source
    import inspect
    import adventure.adventure as advmod
    src = inspect.getsource(advmod)
    assert "@commands.cooldown(rate=1, per=120" in src
    assert "@commands.cooldown(rate=1, per=300" in src
    assert "@commands.cooldown(rate=1, per=600" in src
