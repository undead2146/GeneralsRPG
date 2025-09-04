"""Generate a tree view of a project directory for AI agents.

Usage: python -m tools.tree_view --root . --max-depth 3 --json

Exports:
 - generate_tree(path, max_depth=None, include_hidden=False, follow_symlinks=False)
 - tree_to_text(tree)

The returned `tree` is a dict mapping entry name -> metadata. Directories have a
`children` dict. This shape is easy for agents to consume and serialize to JSON.
"""
from __future__ import annotations

import os
import json
import argparse
from typing import Dict, Any, Optional


def _is_hidden(name: str) -> bool:
    return name.startswith('.')


def generate_tree(path: str, max_depth: Optional[int] = None, include_hidden: bool = False, follow_symlinks: bool = False) -> Dict[str, Any]:
    """Return a dict representing files and directories under `path`.

    - path: root directory to scan
    - max_depth: None for unlimited, 0 for only root entries, 1 for one level deep, etc.
    - include_hidden: whether to include dotfiles/directories
    - follow_symlinks: whether to follow symlinks
    """
    root = os.path.abspath(path)

    def scan(dir_path: str, depth: Optional[int]) -> Dict[str, Any]:
        entries: Dict[str, Any] = {}
        try:
            with os.scandir(dir_path) as it:
                for entry in sorted(it, key=lambda e: e.name.lower()):
                    if not include_hidden and _is_hidden(entry.name):
                        continue

                    try:
                        is_dir = entry.is_dir(follow_symlinks=follow_symlinks)
                    except OSError:
                        # permission or other error
                        is_dir = False

                    if is_dir:
                        node: Dict[str, Any] = {"type": "dir"}
                        if depth is None or depth > 0:
                            node["children"] = scan(entry.path, None if depth is None else depth - 1)
                        else:
                            node["children"] = {}
                    else:
                        try:
                            stat = entry.stat(follow_symlinks=follow_symlinks)
                            node = {"type": "file", "size": stat.st_size}
                        except OSError:
                            node = {"type": "file", "size": None}

                    entries[entry.name] = node
        except FileNotFoundError:
            return {}
        except PermissionError:
            return {}

        return entries

    # If the provided path is a file, return metadata for the file itself
    if os.path.isfile(root):
        try:
            st = os.stat(root)
            return {os.path.basename(root): {"type": "file", "size": st.st_size}}
        except OSError:
            return {os.path.basename(root): {"type": "file", "size": None}}

    return scan(root, max_depth)


def tree_to_text(tree: Dict[str, Any], indent: str = "") -> str:
    lines = []

    for name, meta in tree.items():
        if meta.get("type") == "dir":
            lines.append(f"{indent}{name}/")
            children = meta.get("children", {})
            if children:
                lines.append(tree_to_text(children, indent + "  "))
        else:
            size = meta.get("size")
            size_str = f" ({size} bytes)" if size is not None else ""
            lines.append(f"{indent}{name}{size_str}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a tree view of the project for AI agents")
    parser.add_argument("--root", "-r", default='.', help="Root directory to scan")
    parser.add_argument("--max-depth", "-d", type=int, default=None, help="Maximum recursion depth (0 = root entries only)")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--out", "-o", help="Path to write the output (txt for human, .json for JSON)")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files/directories")
    parser.add_argument("--follow-symlinks", action="store_true", help="Follow symlinks when scanning")

    args = parser.parse_args()

    tree = generate_tree(args.root, max_depth=args.max_depth, include_hidden=args.include_hidden, follow_symlinks=args.follow_symlinks)

    if args.json:
        out = json.dumps(tree, indent=2)
    else:
        out = tree_to_text(tree)

    if args.out:
        try:
            with open(args.out, 'w', encoding='utf-8') as f:
                f.write(out)
        except OSError as e:
            print(f"Failed to write output to {args.out}: {e}")
    else:
        print(out)


if __name__ == '__main__':
    main()
