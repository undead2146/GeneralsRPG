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
    def __init__(self, supplies=0, repair_kits=0, backpack=None):
        self.supplies = supplies
        self.repair_kits = repair_kits
        self.backpack = backpack or {}

    def remove_backpack_item(self, name, count):
        if self.backpack.get(name, 0) >= count:
            self.backpack[name] -= count
            return True
        return False


def test_unitstate_post_init_normalization():
    u = UnitState(id="u1", type="tank", hp=5, max_hp=0)
    assert u.max_hp >= 1
    assert 0 <= u.hp <= u.max_hp


def test_take_damage_and_overflow():
    u = UnitState(id="u2", type="inf", hp=10, max_hp=10)
    overflow = u.take_damage(15)
    assert overflow == 5
    assert u.hp == 0
    assert u.status == "downed"


def test_heal_leftover_and_status_change():
    u = UnitState(id="u3", type="inf", hp=2, max_hp=10)
    leftover = u.heal(12)
    assert leftover == 4
    assert u.hp == 10

    # downed -> healed back to active
    d = UnitState(id="u4", type="inf", hp=0, max_hp=8, status="downed")
    leftover = d.heal(5)
    assert leftover == 0
    assert d.hp == 5
    assert d.status == "active"


def test_serialize_roundtrip():
    units = {
        "a": UnitState(id="a", type="inf", hp=3, max_hp=5),
        "b": UnitState(id="b", type="tank", hp=0, max_hp=12, status="downed"),
    }
    s = units_to_serialized(units)
    restored = units_from_serialized(s)
    assert set(restored.keys()) == set(units.keys())
    assert restored["a"].hp == units["a"].hp
    assert restored["b"].status == "downed"


def test_distribute_incoming_damage():
    units = {
        "u1": UnitState(id="u1", type="inf", hp=5, max_hp=5),
        "u2": UnitState(id="u2", type="inf", hp=10, max_hp=10),
    }
    damage_map, leftover = distribute_incoming_damage(units, 12)
    # u1 should take 5, u2 should take 7, leftover 0
    assert damage_map.get("u1") == 5
    assert damage_map.get("u2") == 7
    assert leftover == 0
    assert units["u1"].status == "downed"


def test_passive_recover():
    units = {
        "u1": UnitState(id="u1", type="inf", hp=0, max_hp=10, status="downed"),
        "u2": UnitState(id="u2", type="inf", hp=0, max_hp=8, status="downed"),
    }
    total = passive_recover(units, recover_per_unit=3)
    assert total == 6
    assert units["u1"].hp == 3
    assert units["u2"].hp == 3


def test_heal_unit_with_supplies_and_without():
    c = DummyChar(supplies=10)
    u = UnitState(id="u5", type="inf", hp=2, max_hp=10)
    ok = heal_unit(u, 5, char=c)
    assert ok is True
    assert c.supplies == 5
    assert u.hp == 7

    # insufficient supplies
    c2 = DummyChar(supplies=1)
    u2 = UnitState(id="u6", type="inf", hp=2, max_hp=10)
    ok = heal_unit(u2, 5, char=c2)
    assert ok is False
    assert c2.supplies == 1


def test_repair_unit_using_kits_and_parts():
    # using a repair kit
    c = DummyChar(repair_kits=1)
    d = UnitState(id="u7", type="tank", hp=0, max_hp=20, status="downed")
    ok = repair_unit(d, char=c, prefer_kit=True)
    assert ok is True
    assert c.repair_kits == 0
    assert d.status == "active"
    assert d.hp >= int(0.4 * d.max_hp)

    # using backpack method with remove_backpack_item
    c2 = DummyChar(backpack={"Parts": 2})
    e = UnitState(id="u8", type="tank", hp=0, max_hp=20, status="downed")
    ok = repair_unit(e, char=c2, prefer_kit=False)
    assert ok is True
    assert c2.backpack.get("Parts", 0) in (1, 0)
    assert e.status == "active"

    # fallback direct decrement
    c3 = DummyChar(backpack={"Parts": 1})
    # remove_backpack_item will succeed, test direct decrement by forcing no method
    del c3.remove_backpack_item
    f = UnitState(id="u9", type="tank", hp=0, max_hp=10, status="downed")
    ok = repair_unit(f, char=c3, prefer_kit=False)
    assert ok is True
    assert c3.backpack.get("Parts", 0) >= 0
    assert f.status == "active"
