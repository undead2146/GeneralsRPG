import json
from pathlib import Path


BASE = Path(__file__).resolve().parents[2] / "adventure" / "data" / "zero_hour"

REQUIRED_FILES = [
    "pets.json",
    "attribs.json",
    "monsters.json",
    "locations.json",
    "raisins.json",
    "threatee.json",
    "tr_set.json",
    "prefixes.json",
    "materials.json",
    "equipment.json",
    "suffixes.json",
    "set_bonuses.json",
    "action_response.json",
    "as_monsters.json",
    "gather.json",
    "salvage.json",
    "blackmarket.json",
]


def test_zero_hour_files_exist_and_non_empty():
    for fname in REQUIRED_FILES:
        fp = BASE / fname
        assert fp.exists(), f"Missing theme file: {fp}"
        data = json.loads(fp.read_text())
        # ensure the root container is non-empty
        if isinstance(data, dict) or isinstance(data, list):
            assert len(data) > 0, f"Empty theme data in {fp}"


def test_monsters_have_hp():
    monsters = json.loads((BASE / "monsters.json").read_text())
    assert isinstance(monsters, dict)
    assert any("hp" in v for v in monsters.values()), "No monster has 'hp' field"


def test_equipment_has_slot():
    equipment = json.loads((BASE / "equipment.json").read_text())
    assert isinstance(equipment, dict)
    # check at least one item contains a slot list
    assert any(isinstance(v.get("slot"), list) for v in equipment.values()), "No equipment entries have 'slot'"


def test_cog_has_alias_methods():
    # Avoid importing the full cog (requires Red packages). Instead inspect
    # the source file for the expected method definitions.
    adv_path = Path(__file__).resolve().parents[2] / "adventure" / "adventure.py"
    src = adv_path.read_text()
    assert "def skirmish(" in src, "Adventure missing skirmish method definition"
    assert "def operation(" in src, "Adventure missing operation method definition"
    assert "def drill(" in src, "Adventure missing drill method definition"
    assert "def gather(" in src, "Adventure missing gather method definition"
    assert "def salvage(" in src, "Adventure missing salvage method definition"
    assert "def blackmarket(" in src, "Adventure missing blackmarket method definition"
