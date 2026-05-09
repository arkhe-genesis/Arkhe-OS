#!/usr/bin/env python3

import os
import shutil

# Directories to create
dirs = ['src', 'docs', 'scripts', 'data']

# Files to keep in root (configurations)
keep_in_root = {
    'README.md', '.gitignore', '.gitattributes', 'package.json', 'package-lock.json',
    'pyproject.toml', 'tsconfig.json', 'pytest.ini', 'Makefile', 'requirements.txt',
    'setup.py', 'LICENSE', 'VERSION', 'CITATION.cff', 'CHANGELOG.md', '.env.example',
    'docker-compose.yml', 'Dockerfile', '.dockerignore', 'netlify.toml', 'vercel.json',
    'migration.sh', 'CLAUDE.md', 'AGENTS.md'
}

# Extensions mappings
extensions = {
    'src': ['.py', '.js', '.ts', '.cpp', '.c', '.h', '.rs', '.go', '.asm', '.f90', '.circom'],
    'docs': ['.md', '.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.xlsx', '.gcode', '.fits'],
    'scripts': ['.sh'],
    'data': ['.csv', '.npz', '.pkl', '.jsonl', '.pt', '.bin', '.plank']
}

# Special files
special_docs = ['arkhe_*.json', 'asic_*.json', 'benchmark_*.json', '*_report.json', '*_log.json']
special_data = ['*.npz', '*.pkl', '*.pt']

def move_file(file_path, dest_dir):
    dest_path = os.path.join(dest_dir, os.path.basename(file_path))
    shutil.move(file_path, dest_path)
    print(f"Moved {file_path} to {dest_path}")

def main():
    # Create directories
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # Get all files in root
    root_files = [f for f in os.listdir('.') if os.path.isfile(f)]

    for file in root_files:
        if file in keep_in_root:
            continue

        ext = os.path.splitext(file)[1].lower()
        moved = False

        # Check extensions
        for dest, exts in extensions.items():
            if ext in exts:
                move_file(file, dest)
                moved = True
                break

        # Special cases
        if not moved:
            if any(file.endswith(s.replace('*', '')) for s in special_docs) or file.endswith('.json'):
                move_file(file, 'docs')
            elif any(file.endswith(s.replace('*', '')) for s in special_data):
                move_file(file, 'data')
            else:
                # Default to src for code files
                if ext in ['.py', '.js', '.ts', '.cpp', '.c', '.h', '.rs', '.go']:
                    move_file(file, 'src')
                else:
                    print(f"Skipped {file}")

if __name__ == "__main__":
    main()