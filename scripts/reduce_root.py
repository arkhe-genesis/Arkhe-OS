#!/usr/bin/env python3

import os
import shutil

# Create directories if not exist
os.makedirs('tools', exist_ok=True)
os.makedirs('components', exist_ok=True)

# Keep these in root
keep_in_root = {'.git', '.github', '.agi', '.asi', '.casi', 'src', 'docs', 'scripts', 'data', 'core', 'substrates', 'runtime', 'contracts', 'models', 'config', 'tests', 'packages', 'archive', 'tools', 'components', 'README.md', 'Makefile', '.gitignore', '.gitattributes', 'LICENSE', 'VERSION', 'CITATION.cff', 'CHANGELOG.md'}

# Move .* directories to tools/
for item in os.listdir('.'):
    if item.startswith('.') and os.path.isdir(item) and item not in keep_in_root:
        print(f"Moving {item} to tools/")
        shutil.move(item, 'tools/')

# Move arkhe-* directories to packages/
for item in os.listdir('.'):
    if item.startswith('arkhe-') and os.path.isdir(item):
        print(f"Moving {item} to packages/")
        shutil.move(item, 'packages/')

# Move other directories to components/
for item in os.listdir('.'):
    dest = 'components/' + item
    if os.path.isdir(item) and item not in keep_in_root and not item.startswith('arkhe-') and not item.startswith('.') and not os.path.exists(dest):
        print(f"Moving {item} to components/")
        shutil.move(item, 'components/')

# Move documentation folders to docs/
doc_folders = ['ARKHE-OS', 'Arkhe', 'Obsidian Ecosystem for Content Creators']
for item in doc_folders:
    if os.path.exists(item):
        print(f"Moving {item} to docs/")
        shutil.move(item, 'docs/')

print("Reorganization complete.")