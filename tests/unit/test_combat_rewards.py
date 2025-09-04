import json
import importlib.util
import os
import sys


def load_module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CURDIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
combat_mod = load_module_from_path("adventure.combat", os.path.join(CURDIR, "adventure", "combat.py"))
rewards_mod = load_module_from_path("adventure.rewards", os.path.join(CURDIR, "adventure", "rewards.py"))

CombatEngine = combat_mod.CombatEngine
RewardEngine = rewards_mod.RewardEngine


def test_combat_deterministic_same_seed():
    session = {
        "fire": [{"id": 1, "name": "Alpha"}],
        "monster_hp": 9999,
    }

    engine1 = CombatEngine(session_snapshot=session, seed=12345)
    engine2 = CombatEngine(session_snapshot=session, seed=12345)

    out1 = engine1.resolve_round()
    out2 = engine2.resolve_round()

    assert out1.total_damage == out2.total_damage
    assert out1.messages == out2.messages


def test_rewards_deterministic_with_seed():
    base = os.path.join(os.path.dirname(__file__), "..", "adventure", "data", "zero_hour")
    # compute path relative to repo root
    cfg_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "adventure", "data", "zero_hour", "rewards.json"))
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    participants = [{"id": 10, "name": "Bravo"}, {"id": 11, "name": "Charlie"}]

    r1 = RewardEngine(cfg, seed=999)
    r2 = RewardEngine(cfg, seed=999)

    rewards1 = r1.calculate("skirmish", participants, None)
    rewards2 = r2.calculate("skirmish", participants, None)

    assert rewards1 == rewards2

