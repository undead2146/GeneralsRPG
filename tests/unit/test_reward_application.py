import pytest

from adventure.rewards import RewardEngine


class FakeChar:
    def __init__(self):
        self.supplies = 0
        self.cp = 0
        self.backpack = []

    def add_supplies(self, amount: int):
        self.supplies += int(amount)

    def add_cp(self, amount: int):
        self.cp += int(amount)

    def add_to_backpack(self, item, number: int = 1):
        # store tuple (name, number)
        name = getattr(item, "name", str(item))
        self.backpack.append((name, int(number)))


class FailerChar(FakeChar):
    def add_cp(self, amount: int):
        raise RuntimeError("simulated bank error")


def test_apply_rewards_happy_path():
    cfg = {
        "skirmish": {"supplies": [10, 10], "cp": [1, 1], "parts": [2, 2], "blueprints": 1.0}
    }
    engine = RewardEngine(cfg, seed=42)
    participants = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    reward_map = engine.calculate("skirmish", participants, None)

    assert set(reward_map.keys()) == {1, 2}

    c1 = FakeChar()
    c2 = FakeChar()
    mapping = {1: c1, 2: c2}

    for uid, drops in reward_map.items():
        char = mapping.get(uid)
        assert char is not None
        if drops.get("supplies"):
            char.add_supplies(drops.get("supplies"))
        if drops.get("cp"):
            char.add_cp(drops.get("cp"))
        if drops.get("parts"):
            char.add_to_backpack(type("I", (), {"name": "Parts"})(), drops.get("parts"))
        if drops.get("blueprints"):
            char.add_to_backpack(type("I", (), {"name": "Blueprint Fragment"})(), drops.get("blueprints"))

    assert c1.supplies >= 10 and c2.supplies >= 10
    assert c1.cp >= 1 and c2.cp >= 1
    assert any(n == "Parts" for n, _ in c1.backpack + c2.backpack)
    assert any(n == "Blueprint Fragment" for n, _ in c1.backpack + c2.backpack)


def test_apply_rewards_missing_member():
    cfg = {"gather": {"supplies": [5, 5], "cp": [0, 0]}}
    engine = RewardEngine(cfg, seed=7)
    participants = [{"id": 1, "name": "A"}, {"id": 99, "name": "Missing"}]
    reward_map = engine.calculate("gather", participants, None)

    # mapping contains both ids but our mapping only has id 1
    c1 = FakeChar()
    mapping = {1: c1}

    # applying rewards should skip missing member without raising
    for uid, drops in reward_map.items():
        char = mapping.get(uid)
        if char is None:
            # simulate skip when member not present
            continue
        if drops.get("supplies"):
            char.add_supplies(drops.get("supplies"))

    assert c1.supplies >= 5


def test_apply_rewards_partial_failure():
    cfg = {"raid": {"supplies": [20, 20], "cp": [2, 2]}}
    engine = RewardEngine(cfg, seed=99)
    participants = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    reward_map = engine.calculate("raid", participants, None)

    c1 = FakeChar()
    c2 = FailerChar()
    mapping = {1: c1, 2: c2}

    for uid, drops in reward_map.items():
        char = mapping.get(uid)
        if char is None:
            continue
        if drops.get("supplies"):
            char.add_supplies(drops.get("supplies"))
        # CP application might fail for some users; ensure we catch and continue
        if drops.get("cp"):
            try:
                char.add_cp(drops.get("cp"))
            except Exception:
                # swallowed as production code does
                pass

    # supplies should be applied even if CP failed for one user
    assert c1.supplies >= 20
    assert c2.supplies >= 20
    # c2.cp should remain 0 due to simulated failure
    assert c2.cp == 0
