"""
hook-numpy.py — Força import de numpy.core._multiarray_umath
"""
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['numpy.core._multiarray_umath']
hiddenimports += collect_submodules('numpy')