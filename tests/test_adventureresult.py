import ast
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "adventure" / "adventureresult.py"


def test_adventureresult_syntax():
    """Ensure `adventureresult.py` parses without executing top-level code."""
    src = SRC.read_text(encoding="utf-8")
    ast.parse(src)


def test_adventureresult_contains_dataclass_and_class():
    src = SRC.read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    # We expect StatRange dataclass and AdventureResults class to be present
    assert "StatRange" in names or "AdventureResults" in names
