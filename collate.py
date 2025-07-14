import os

def collate_py_files(root_folder, output_file):
    with open(output_file, 'w', encoding='utf-8') as out:
        for dirpath, _, filenames in os.walk(root_folder):
            for fname in filenames:
                if fname.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(dirpath, fname), root_folder)
                    out.write(f"\n\n### FILE: {rel_path}\n\n")
                    try:
                        with open(os.path.join(dirpath, fname), 'r', encoding='utf-8') as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"\n[ERROR reading {rel_path}: {e}]\n")

if __name__ == "__main__":
    collate_py_files("soul", "all_code_soul_py.txt")
    print("Collated all .py files in 'soul/' into all_code_soul_py.txt")
