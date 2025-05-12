# src/tools/dev/generate_tree.py

"""
Project Tree Generator

Recursively walks the project directory to build a directory-tree
representation, excluding common build/test folders, and writes the
output to a specified file.
"""

import os
from pathlib import Path
from typing import List, Set

# === Configuration ===

EXCLUDED_DIRS: Set[str] = {'.pytest_cache', '__pycache__', '.git', '.vscode'}
INDENT_UNIT: str = "    "
OUTPUT_FILE: Path = Path("docs/system/project_tree.txt")


def generate_tree(
    dir_path: Path,
    prefix: str = "",
    lines: List[str] | None = None
) -> None:
    """
    Recursively append directory and file entries under dir_path into lines.

    Args:
        dir_path (Path): Directory to traverse.
        prefix (str): Leading whitespace and connectors for current level.
        lines (List[str] | None): Collector for output lines.
    """
    if lines is None:
        return

    entries = sorted(
        e for e in dir_path.iterdir()
        if e.name not in EXCLUDED_DIRS
    )
    total = len(entries)

    for index, entry in enumerate(entries, start=1):
        connector = "└── " if index == total else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = INDENT_UNIT if index == total else "│   "
            generate_tree(entry, prefix + extension, lines)


def main() -> None:
    """
    Build the project tree starting from the current working directory
    and write it to OUTPUT_FILE.
    """
    root = Path.cwd()
    root_name = root.name
    lines: List[str] = [f"{root_name}/"]

    generate_tree(root, lines=lines)

    # Ensure the output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write the tree structure to the output file
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Project tree written to '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()
