"""Unit helpers for Generals Zero Hour themed mechanics.

Provides a small UnitState representation and helper functions to apply
incoming damage to an army, recover downed units, and serialize/deserialize
unit state. This is intentionally minimal to integrate with the existing
Character persistence and to keep unit logic unit-testable.
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple


@dataclass
class UnitState:
    id: str
    type: str
    hp: int
    max_hp: int
    status: str = "active"  # active | downed | destroyed
    vet: int = 0

    def __post_init__(self):
        """Normalize fields after construction to keep invariants."""
        # Ensure sensible max_hp
        if not isinstance(self.max_hp, int) or self.max_hp <= 0:
            self.max_hp = max(1, int(self.hp) if isinstance(self.hp, int) and self.hp > 0 else 1)
        # Bound hp
        self.hp = max(0, min(self.hp, self.max_hp))
        # Normalize status
        if self.hp <= 0 and self.status == "active":
            self.status = "downed"
        if self.hp > 0 and self.status == "downed":
            self.status = "active"

    @property
    def unit_type(self) -> str:
        """Compatibility alias for the `type` field.

        Some callers prefer `unit.unit_type` to avoid shadowing the builtin
        name `type`. Expose both to remain compatible.
        """
        return self.type

    def take_damage(self, amount: int) -> int:
        """Apply damage to this unit and return overflow damage (if any).

        The unit will become 'downed' if hp <= 0. Overflow is non-negative
        and should be distributed to remaining units.
        """
        if self.status != "active":
            return amount
        self.hp -= amount
        if self.hp <= 0:
            overflow = -self.hp
            self.hp = 0
            self.status = "downed"
            return overflow
        return 0

    def heal(self, amount: int) -> int:
        """Heal this unit and return leftover heal if it would exceed max_hp."""
        if self.status == "destroyed":
            return amount
        self.hp += amount
        if self.hp > self.max_hp:
            leftover = self.hp - self.max_hp
            self.hp = self.max_hp
            if self.status == "downed" and self.hp > 0:
                self.status = "active"
            return leftover
        if self.status == "downed" and self.hp > 0:
            self.status = "active"
        return 0


def units_from_serialized(data: Dict[str, Dict]) -> Dict[str, UnitState]:
    """Deserialize a mapping of unit id -> dict into UnitState instances."""
    out = {}
    for uid, entry in data.items():
        out[uid] = UnitState(
            id=uid,
            type=entry.get("type", "unknown"),
            hp=int(entry.get("hp", 0)),
            max_hp=int(entry.get("max_hp", entry.get("hp", 0) or 1)),
            status=entry.get("status", "active"),
            vet=int(entry.get("vet", 0)),
        )
    return out


def units_to_serialized(units: Dict[str, UnitState]) -> Dict[str, Dict]:
    """Serialize UnitState instances into simple dicts for persistence."""
    return {uid: asdict(u) for uid, u in units.items()}


def distribute_incoming_damage(units: Dict[str, UnitState], incoming: int) -> Tuple[Dict[str, int], int]:
    """Distribute incoming damage across active units.

    Returns a tuple (damage_map, leftover) where damage_map is a mapping of
    unit id -> damage applied and leftover is remaining overflow damage
    after all units are downed.
    """
    damage_map: Dict[str, int] = {}
    if incoming <= 0:
        return damage_map, 0
    # Simple distribution: iterate active units in insertion order and apply
    # damage until exhausted. This can be replaced with more advanced
    # frontline/formation logic later.
    for uid, unit in list(units.items()):
        if incoming <= 0:
            break
        if unit.status != "active":
            continue
        # apply as much as needed to down the unit
        needed = unit.hp
        applied = min(needed, incoming)
        overflow = unit.take_damage(applied)
        damage_map[uid] = applied - overflow
        incoming -= (applied - overflow)
    return damage_map, incoming


def passive_recover(units: Dict[str, UnitState], recover_per_unit: int = 1) -> int:
    """Apply passive recovery to all downed units. Returns total healed amount."""
    total = 0
    for unit in units.values():
        if unit.status == "downed":
            leftover = unit.heal(recover_per_unit)
            healed = recover_per_unit - leftover
            total += healed
    return total


def heal_unit(unit: UnitState, amount: int, char=None) -> bool:
    """Heal an active unit using supplies from char (if provided).

    Returns True if healing was applied, False otherwise.
    """
    if unit.status != "active":
        return False
    if char and getattr(char, "supplies", 0) < amount:
        return False
    if char:
        # reduce supplies; tests expect integer arithmetic
        char.supplies -= amount
    unit.hp = min(unit.max_hp, unit.hp + amount)
    return True


def repair_unit(unit: UnitState, char=None, prefer_kit=True) -> bool:
    """Repair a downed unit using repair kits or parts.

    prefer_kit controls whether repair kits are consumed before backpack parts.
    Returns True on successful repair (unit becomes active), False otherwise.
    """
    if unit.status != "downed":
        return False
    if prefer_kit and getattr(char, "repair_kits", 0) > 0:
        char.repair_kits -= 1
        unit.hp = max(unit.hp, int(0.4 * unit.max_hp))
        unit.status = "active"
        return True
    if char and getattr(char, "backpack", {}).get("Parts", 0) > 0:
        # prefer character method to remove backpack items if available
        if hasattr(char, "remove_backpack_item") and char.remove_backpack_item("Parts", 1):
            unit.hp = max(unit.hp, int(0.25 * unit.max_hp))
            unit.status = "active"
            return True
        # fallback: directly decrement backpack count
        bp = getattr(char, "backpack", None)
        if isinstance(bp, dict) and bp.get("Parts", 0) > 0:
            bp["Parts"] -= 1
            unit.hp = max(unit.hp, int(0.25 * unit.max_hp))
            unit.status = "active"
            return True
    return False
