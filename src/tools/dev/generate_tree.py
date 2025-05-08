import os

# Exclude common directories
EXCLUDED = {'.pytest_cache', '__pycache__', '.git', '.vscode'}
INDENT_UNIT = "    "

# Use a relative path (no leading slash) and allow customizing if desired
OUTPUT_FILE = "docs/system/project_tree.txt"


def generate_tree(dir_path, prefix="", lines=None):
    entries = sorted(e for e in os.listdir(dir_path) if e not in EXCLUDED)
    for i, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        connector = "└── " if i == len(entries) - 1 else "├── "
        lines.append(prefix + connector + entry)
        if os.path.isdir(path):
            extension = INDENT_UNIT if i == len(entries) - 1 else "│   "
            generate_tree(path, prefix + extension, lines)


if __name__ == "__main__":
    # Initialize the tree with the root folder name
    root_name = os.path.basename(os.path.abspath("."))
    lines = [f"{root_name}/"]
    generate_tree(".", lines=lines)

    # Ensure the output directory exists
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write the tree structure to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Project tree written to '{OUTPUT_FILE}'")
