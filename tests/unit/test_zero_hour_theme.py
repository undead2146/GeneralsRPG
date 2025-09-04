import json
from pathlib import Path


def test_zero_hour_theme_files_exist_and_parse():
    repo = Path(__file__).resolve().parents[2]
    base = repo / "adventure" / "data" / "zero_hour"
    files = {
        "gather.json": "drops",
        "salvage.json": "drops",
        "blackmarket.json": "drops",
        "rewards.json": None,
        "recipes.json": None,
    }
    for fname, expected_key in files.items():
        fp = base / fname
        assert fp.exists(), f"{fname} is missing from zero_hour theme"
        data = json.loads(fp.read_text(encoding="utf-8"))
        if expected_key:
            assert expected_key in data, f"{fname} missing expected key: {expected_key}"


def test_recipes_contain_tank():
    repo = Path(__file__).resolve().parents[2]
    fp = repo / "adventure" / "data" / "zero_hour" / "recipes.json"
    data = json.loads(fp.read_text(encoding="utf-8"))
    assert "tank" in data, "recipes.json must contain a 'tank' recipe"
