"""
hook-scipy.py — Força inclusão de sub‑módulos BLAS/LAPACK.
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('scipy.linalg')
hiddenimports += collect_submodules('scipy.sparse.linalg')