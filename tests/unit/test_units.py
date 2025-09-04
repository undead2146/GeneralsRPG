import time
import pytest

from adventure.units import UnitState, units_to_serialized, units_from_serialized, heal_unit, repair_unit, passive_recover


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


@pytest.fixture
def simple_unit():
    u = UnitState(id_="u1", type_="Infantry", hp=50, max_hp=100, status="active", vet=0)
    return u


def test_heal_not_downed(simple_unit):
    # heal should increase hp but not exceed max
    char = DummyChar()
    char.supplies = 100
    healed = heal_unit(simple_unit, amount=30, char=char)
    assert healed is True
    assert simple_unit.hp == 80

    # heal beyond max
    healed = heal_unit(simple_unit, amount=50, char=char)
    assert healed is True
    assert simple_unit.hp == 100


def test_heal_downed_noop():
    u = UnitState(id_="u2", type_="Vehicle", hp=0, max_hp=200, status="downed", vet=0)
    char = DummyChar()
    char.supplies = 100
    # heal should not affect downed units in this implementation
    healed = heal_unit(u, amount=50, char=char)
    assert healed is False
    assert u.hp == 0


def test_repair_with_kit_revivify():
    u = UnitState(id_="u3", type_="Vehicle", hp=0, max_hp=200, status="downed", vet=0)
    char = DummyChar()
    char.repair_kits = 1
    repaired = repair_unit(u, char=char, prefer_kit=True)
    assert repaired is True
    # kit should restore at least 40% of max (80)
    assert u.hp >= int(0.4 * u.max_hp)
    assert u.status == "active"
    assert char.repair_kits == 0


def test_repair_with_parts_revivify():
    u = UnitState(id_="u4", type_="Vehicle", hp=0, max_hp=200, status="downed", vet=0)
    char = DummyChar()
    char.backpack = {"Parts": 3}
    repaired = repair_unit(u, char=char, prefer_kit=False)
    assert repaired is True
    # parts should restore at least 25% (50)
    assert u.hp >= int(0.25 * u.max_hp)
    assert u.status == "active"
    assert char.backpack.get("Parts", 0) == 0


def test_passive_recover_tick():
    # unit should recover 15% of max when tick is due
    now = int(time.time())
    u = UnitState(id_="u5", type_="Infantry", hp=50, max_hp=100, status="active", vet=0)
    # set next_tick to past
    u.next_tick_at = now - 10
    changed = passive_recover([u], now)
    assert changed is True
    assert u.hp > 50
    # expect increase by at least int(0.15*100) = 15
    assert u.hp >= 65
