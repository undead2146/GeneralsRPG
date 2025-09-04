import os
from tools.tree_view import generate_tree, tree_to_text


def test_generate_tree_root(tmp_path):
    # create a small folder tree
    d = tmp_path / "proj"
    d.mkdir()
    (d / "file1.txt").write_text("hello")
    sub = d / "subdir"
    sub.mkdir()
    (sub / "file2.txt").write_text("world")

    tree = generate_tree(str(d), max_depth=2)
    assert "file1.txt" in tree
    assert "subdir" in tree
    assert tree["file1.txt"]["type"] == "file"
    assert tree["subdir"]["type"] == "dir"

    txt = tree_to_text(tree)
    assert "file1.txt" in txt
    assert "subdir/" in txt
