import os

# CONFIG — Set this to your main project folder (absolute or relative)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(PROJECT_DIR, '_ALL_SCRIPTS.txt')

def get_all_py_files(base_dir):
    py_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                py_files.append(full_path)
    return py_files

def collate_scripts(py_files, output_file):
    with open(output_file, 'w', encoding='utf-8') as out:
        for path in py_files:
            out.write(f"\n\n\n# ====== FILE: {path} ======\n\n")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    out.write(f.read())
            except Exception as e:
                out.write(f"# ERROR READING FILE: {e}\n")

def main():
    py_files = get_all_py_files(PROJECT_DIR)
    print(f"Found {len(py_files)} Python files. Collating…")
    collate_scripts(py_files, OUTPUT_FILE)
    print(f"All scripts written to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
