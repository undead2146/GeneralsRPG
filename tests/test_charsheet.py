import ast
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "adventure" / "charsheet.py"


def test_charsheet_syntax():
    """Confirm that `charsheet.py` parses as valid Python (avoids executing imports)."""
    src = SRC.read_text(encoding="utf-8")
    ast.parse(src)


def test_charsheet_has_character_class():
    src = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src)
    assert any(isinstance(node, ast.ClassDef) and node.name == "Character" for node in tree.body)
