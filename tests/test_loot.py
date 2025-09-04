import ast
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "adventure" / "loot.py"


def test_loot_syntax():
    src = SRC.read_text(encoding="utf-8")
    ast.parse(src)


def test_loot_contains_lootcommands():
    src = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src)
    assert any(isinstance(node, ast.ClassDef) and node.name == "LootCommands" for node in tree.body)
