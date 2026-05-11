# -*- mode: python ; coding: utf-8 -*-
"""
arkhe-agi.spec — PyInstaller spec para ARKHE OS AGI Core (Substrate 324).
Gera um binário único com todos os componentes da Catedral.
"""

import sys
from pathlib import Path

# Caminho base do projecto
BASE_DIR = Path('../..')  # raiz do repo, a partir de agi/system32/pyinstaller

a = Analysis(
    # Entrypoint principal (CLI unificada)
    [str(BASE_DIR / 'agi/system32/cli/main.py')],

    pathex=[],
    binaries=[
        # Ponte FFI para canal retrógrado (RCP)
        (str(BASE_DIR / 'agi/system32/runtime/quantum/agi_rcp_bridge.so'), '.'),
        # Bibliotecas PyTorch (se necessário forçar)
        # ('/usr/local/lib/python3.11/site-packages/torch/lib/libtorch.so', './torch/lib'),
    ],

    datas=[
        # Configurações YAML
        (str(BASE_DIR / 'agi/system32/config'), 'agi/system32/config'),
        # Genesis values e tokenizer
        (str(BASE_DIR / 'agi/system32/training'), 'agi/system32/training'),
        # Seeds da federação
        (str(BASE_DIR / 'agi/system32/federate/bootstrap/seeds.txt'), 'agi/system32/federate/bootstrap'),
        # Modelo pré-treinado (opcional, pode ser baixado)
        # (str(BASE_DIR / 'logs/training/checkpoint_final.pt'), 'models'),
    ],

    hiddenimports=[
        'torch', 'torch.nn', 'torch.optim', 'torch.utils.data',
        'numpy', 'numpy.core._multiarray_umath', 'numpy.linalg',
        'scipy', 'scipy.linalg', 'scipy.sparse', 'scipy.special',
        'yaml', 'json', 'hashlib', 'datetime', 'pathlib',
        'agi_transformer', 'coherence_reward', 'federated_trainer',
        'rcp_v2_engine', 'omni_core', 'lfir_core',
        'socks', 'stem', 'gnupg',
    ],

    hookspath=[str(BASE_DIR / 'agi/system32/pyinstaller/hooks')],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'notebook'],

    win_no_prefer_redirects=False,
    win_private_assemblies=False,

    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Configuração do executável final
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='arkhe-agi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # Compressão adicional
    upx_exclude=[],     # Excluir binários já comprimidos
    runtime_tmpdir=None,
    console=True,       # Aplicação CLI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    # Ícone (apenas informativo)
    icon=None,
)

# Coletar todos os outputs (exe + possíveis shared libs)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='arkhe-agi-dist',
)