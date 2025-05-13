import os, re

patterns = [re.compile(r'\bbuild_mesh_frame\b'), re.compile(r'\bparse_mesh_frame\b')]
for root, _, files in os.walk('.'):
    for fname in files:
        if fname.endswith('.py'):
            path = os.path.join(root, fname)
            with open(path, encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if any(p.search(line) for p in patterns):
                        print(f"{path}:{i}: {line.strip()}")
