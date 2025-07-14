import os

OUTPUT_FILE = "all_code_soul_py.txt"

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for dirpath, _, filenames in os.walk("."):
        for fname in filenames:
            if fname.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(dirpath, fname), ".")
                out.write(f"\n\n### FILE: {rel_path}\n\n")
                try:
                    with open(os.path.join(dirpath, fname), "r", encoding="utf-8") as f:
                        out.write(f.read())
                except Exception as e:
                    out.write(f"\n[ERROR reading {rel_path}: {e}]\n")

print(f"Collated all .py files into {OUTPUT_FILE}")
