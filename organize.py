import os
import shutil

# Extensions and their target directories
mapping = {
    ".py": "python/scripts",
    ".js": "scripts/js",
    ".ts": "scripts/ts",
    ".cjs": "scripts/js",
    ".mjs": "scripts/js",
    ".sh": "scripts/shell",
    ".json": "config/json",
    ".yaml": "config/yaml",
    ".yml": "config/yaml",
    ".md": "docs/markdown",
    ".txt": "docs/reports",
    ".pdf": "docs/reports",
    ".html": "docs/reports",
    ".png": "docs/images",
    ".jpg": "docs/images",
    ".jpeg": "docs/images",
    ".svg": "docs/images",
    ".csv": "data/csv",
    ".xlsx": "data/excel",
    ".npz": "data/numpy",
    ".pkl": "data/pickle",
    ".log": "data/logs",
    ".gcode": "data/gcode",
    ".bin": "data/bin",
    ".cpp": "src/cpp",
    ".c": "src/c",
    ".h": "src/c",
    ".glsl": "src/glsl",
    ".asm": "src/asm",
    ".circom": "src/circom",
    ".f90": "src/fortran",
    ".go": "src/go",
    ".v": "src/verilog",
    ".plank": "src/plank",
    ".pt": "data/models",
    ".mtp3": "data/misc",
    ".arkhe": "scripts/misc",
    ".patch": "scripts/misc",
    ".tcl": "scripts/misc",
    ".so": "lib/shared",
    ".ini": "config/ini",
    ".properties": "config/properties",
    ".toml": "config/toml",
    ".gz": "data/archives"
}

# Directories to ignore
ignore_dirs = {".git", ".venv", "node_modules", "__pycache__"}

# Files to keep in the root
keep_files = {
    "README.md",
    "README_track3.md",
    "README_v158.md",
    "README_v340_4.md",
    "README_v402_3.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "CLAUDE.md",
    "DESIGN.md",
    "DREAMS.md",
    "FINAL_RELEASE_GUIDE.md",
    "HUMAN_CIVILIZATION_3D_MODELING.md",
    "IMPLEMENTATION_SUMMARY_v3_0_OMEGA.md",
    "MANIFESTO_Z.md",
    "MELT_PROTOCOL.md",
    "MEMORY.md",
    "QUICK_START_GUIDE.md",
    "SECURITY_AUDIT_REPORT.md",
    "LICENSE",
    "VERSION",
    "config.yaml",
    "requirements.txt",
    "requirements-mesh.txt",
    "requirements-neuro.txt",
    "requirements-ontology.txt",
    "requirements-tau.txt",
    "pre_commit.sh",
    "setup.py",
    "pytest.ini",
    "Makefile",
    "CMakeLists.txt",
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "eslint.config.mjs",
    "vite.config.ts",
    "docker-compose.yml",
    "docker-compose.swarm.yml",
    "Dockerfile",
    "Dockerfile.mesh-node",
    "Dockerfile.python",
    "Dockerfile.relayer",
    ".gitignore",
    ".gitmodules",
    ".gitattributes",
    ".dockerignore",
    ".editorconfig",
    ".env.example",
    "organize.py"
}

def organize_files():
    root_dir = "."
    moved_count = 0
    updated_readme = False

    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)

        if os.path.isfile(item_path):
            if item in keep_files or item.startswith("."):
                continue

            _, ext = os.path.splitext(item)
            ext = ext.lower()

            target_dir = mapping.get(ext)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, item)
                print(f"Moving {item} -> {target_dir}/")
                shutil.move(item_path, target_path)
                moved_count += 1
            else:
                # Handle special cases without extension mapping or fallback
                if item == "wget-log":
                    os.makedirs("data/logs", exist_ok=True)
                    shutil.move(item_path, os.path.join("data/logs", item))
                    moved_count += 1
                elif item == "CITATION.cff":
                    os.makedirs("docs/misc", exist_ok=True)
                    shutil.move(item_path, os.path.join("docs/misc", item))
                    moved_count += 1
                elif "test" in item.lower():
                    os.makedirs("tests", exist_ok=True)
                    shutil.move(item_path, os.path.join("tests", item))
                    moved_count += 1
                else:
                    # Move everything else to misc to clean up the root
                    os.makedirs("misc", exist_ok=True)
                    shutil.move(item_path, os.path.join("misc", item))
                    moved_count += 1

    print(f"Organized {moved_count} files.")

    # Update README.md
    readme_path = "README.md"
    if os.path.exists(readme_path):
        with open(readme_path, "a") as f:
            f.write("\n\n## Repository Organization\n\n")
            f.write("Files have been organized into the following directory structure for better coherence:\n")
            f.write("- **python/scripts/**: Python scripts.\n")
            f.write("- **scripts/js/**: JavaScript/TypeScript scripts.\n")
            f.write("- **scripts/shell/**: Shell scripts.\n")
            f.write("- **config/json/**: JSON configuration files.\n")
            f.write("- **config/yaml/**: YAML configuration files.\n")
            f.write("- **docs/markdown/**: Markdown documentation files.\n")
            f.write("- **docs/reports/**: Text, PDF, and HTML report files.\n")
            f.write("- **docs/images/**: Image files (PNG, JPG, SVG).\n")
            f.write("- **data/csv/**: CSV data files.\n")
            f.write("- **data/excel/**: Excel data files.\n")
            f.write("- **data/numpy/**: Numpy data files.\n")
            f.write("- **data/pickle/**: Pickle data files.\n")
            f.write("- **data/logs/**: Log files.\n")
            f.write("- **data/gcode/**: GCode files.\n")
            f.write("- **data/bin/**: Binary files.\n")
            f.write("- **src/cpp/**: C++ source files.\n")
            f.write("- **src/c/**: C source and header files.\n")
            f.write("- **src/glsl/**: GLSL shader files.\n")
            f.write("- **src/asm/**: Assembly files.\n")
            f.write("- **src/circom/**: Circom circuits.\n")
            f.write("- **src/fortran/**: Fortran source files.\n")
            f.write("- **src/go/**: Go source files.\n")
            f.write("- **src/verilog/**: Verilog source files.\n")
            f.write("- **src/plank/**: Plank source files.\n")
            f.write("- **data/models/**: Model files (.pt).\n")
            f.write("- **data/misc/**: Miscellaneous data files (.mtp3).\n")
            f.write("- **scripts/misc/**: Miscellaneous scripts (.arkhe, .patch, .tcl).\n")
            f.write("- **lib/shared/**: Shared libraries (.so).\n")
            f.write("- **tests/**: Test-related files.\n")
            f.write("- **misc/**: Uncategorized files.\n")
        updated_readme = True

    if updated_readme:
        print("Updated README.md with repository organization structure.")

if __name__ == "__main__":
    organize_files()
