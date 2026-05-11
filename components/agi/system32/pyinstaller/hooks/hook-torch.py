"""
hook-torch.py — Garante que PyTorch e suas bibliotecas nativas sejam incluídas.
"""
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Incluir as shared libraries do torch
binaries = collect_dynamic_libs('torch')

# Incluir dados do torch (ex: _C.so)
datas = collect_data_files('torch')