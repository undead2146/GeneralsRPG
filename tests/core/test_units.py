import pytest
from typing import Dict

from adventure.core.units import (
    UnitState,
    units_from_serialized,
    units_to_serialized,
    distribute_incoming_damage,
    passive_recover,
    heal_unit,
    repair_unit,
)


class DummyChar:
    def __init__(self):
        self.supplies = 0
        self.repair_kits = 0
        self.backpack = {}

    def remove_backpack_item(self, name: str, count: int) -> bool:
        cur = self.backpack.get(name, 0)
        if cur < count:
            return False
        self.backpack[name] = cur - count
        return True


def test_unitstate_post_init_normalization():
    # max_hp <= 0 should be normalized to at least hp (or 1)
    u = UnitState(id="u1", type="Infantry", hp=10, max_hp=0)
    assert u.max_hp >= 1
    assert u.max_hp == 10
    assert u.hp == 10

    # hp should be bounded to max_hp
    u2 = UnitState(id="u2", type="Tank", hp=999, max_hp=50)
    assert u2.hp == 50


def test_take_damage_and_overflow_and_status():
    u = UnitState(id="u3", type="Infantry", hp=5, max_hp=10)
    overflow = u.take_damage(8)
    assert u.hp == 0
    assert u.status == "downed"
    assert overflow == 3

    # non-active units ignore damage (return incoming back)
    overflow2 = u.take_damage(2)
    assert overflow2 == 2


def test_heal_method_and_leftover():
    u = UnitState(id="u4", type="Infantry", hp=0, max_hp=20, status="downed")
    leftover = u.heal(5)
    # healed 5, now hp==5 and status should be active
    assert leftover == 0
    assert u.hp == 5
    assert u.status == "active"

    # heal beyond max produces leftover
    leftover2 = u.heal(100)
    assert leftover2 == 85
    assert u.hp == u.max_hp


def test_serialization_roundtrip():
    units: Dict[str, UnitState] = {
        "a": UnitState(id="a", type="Inf", hp=10, max_hp=20),
        "b": UnitState(id="b", type="Veh", hp=0, max_hp=50, status="downed"),
    }
    data = units_to_serialized(units)
    back = units_from_serialized(data)
    assert set(back.keys()) == set(units.keys())
    assert back["a"].hp == 10
    assert back["b"].status == "downed"


def test_distribute_incoming_damage_and_leftover():
    units = {
        "u1": UnitState(id="u1", type="Inf", hp=5, max_hp=5),
        "u2": UnitState(id="u2", type="Inf", hp=7, max_hp=7),
        "u3": UnitState(id="u3", type="Inf", hp=3, max_hp=3),
    }
    dmg_map, leftover = distribute_incoming_damage(units, 10)
    # should have downed the first unit (5) and applied 5 to the second
    assert dmg_map.get("u1") == 5
    assert dmg_map.get("u2") == 5
    assert leftover == 0
    assert units["u1"].status == "downed"
    assert units["u2"].hp == 2

    dmg_map2, leftover2 = distribute_incoming_damage(units, 100)
    # all should be downed and leftover returned
    assert leftover2 >= 0
    assert all(u.status == "downed" or u.status == "destroyed" for u in units.values())


def test_passive_recover():
    u = UnitState(id="u5", type="Inf", hp=0, max_hp=20, status="downed")
    total = passive_recover({"u5": u}, recover_per_unit=5)
    assert total == 5
    assert u.hp == 5
    assert u.status == "active"


def test_heal_unit_with_char_supplies():
    u = UnitState(id="u6", type="Inf", hp=50, max_hp=100, status="active")
    c = DummyChar()
    c.supplies = 30
    ok = heal_unit(u, amount=20, char=c)
    assert ok is True
    assert u.hp == 70
    assert c.supplies == 10

    # not enough supplies
    c2 = DummyChar()
    c2.supplies = 5
    ok2 = heal_unit(u, amount=10, char=c2)
    assert ok2 is False


def test_repair_unit_using_kit_and_parts():
    u = UnitState(id="u7", type="Veh", hp=0, max_hp=100, status="downed")
    c = DummyChar()
    c.repair_kits = 1
    repaired = repair_unit(u, char=c, prefer_kit=True)
    assert repaired is True
    assert u.status == "active"
    assert c.repair_kits == 0

    u2 = UnitState(id="u8", type="Veh", hp=0, max_hp=80, status="downed")
    c2 = DummyChar()
    c2.backpack = {"Parts": 1}
    repaired2 = repair_unit(u2, char=c2, prefer_kit=False)
    assert repaired2 is True
    assert u2.status == "active"
    assert c2.backpack.get("Parts", 0) == 0
