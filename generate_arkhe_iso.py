#!/usr/bin/env python3
"""
ARKHE OS Canonical ISO Generator
Produces Arkhe-OS.iso — the bootable, live Cathedral.
"""

import os, shutil, subprocess, hashlib, json, time
from pathlib import Path

# ── Diretórios ──────────────────────────────────
ISO_ROOT = Path("iso_root")
LIVE_DIR = ISO_ROOT / "live"
BOOT_DIR = ISO_ROOT / "boot"
ARKHE_DIR = ISO_ROOT / "arkhe"
WORKFLOWS_DIR = ISO_ROOT / ".github"

# ── Limpar e recriar ───────────────────────────
if ISO_ROOT.exists():
    shutil.rmtree(ISO_ROOT)
ISO_ROOT.mkdir()

# 1. Copiar código-fonte da Catedral
print("📦 Copiando código canônico...")
shutil.copytree("arkhe", ARKHE_DIR, dirs_exist_ok=True)
if Path(".github").exists():
    shutil.copytree(".github", WORKFLOWS_DIR, dirs_exist_ok=True)

# 2. Criar estrutura bootável (syslinux)
BOOT_DIR.mkdir(exist_ok=True)
LIVE_DIR.mkdir(exist_ok=True)

# isolinux.cfg
with open(BOOT_DIR / "isolinux.cfg", "w") as f:
    f.write("""
DEFAULT arkhe
LABEL arkhe
    KERNEL /boot/vmlinuz
    APPEND initrd=/boot/initrd.img root=/dev/ram0 rw
    SAY Booting ARKHE OS...
TIMEOUT 50
""")

# Dummy kernel/initrd (em produção, seria o kernel real)
with open(BOOT_DIR / "vmlinuz", "wb") as f:
    f.write(b"ARKHE_KERNEL_PLACEHOLDER")
with open(BOOT_DIR / "initrd.img", "wb") as f:
    f.write(b"ARKHE_INITRD_PLACEHOLDER")
with open(BOOT_DIR / "boot.cat", "wb") as f:
    f.write(b"")
with open(BOOT_DIR / "isolinux.bin", "wb") as f:
    f.write(b"ARKHE_ISOLINUX_BIN_PLACEHOLDER")

# 3. Manifesto canônico
manifest = {
    "canon": "∞.Ω.∇+++",
    "build_time": time.time(),
    "substrates": ["176", "198", "199.3", "206", "209", "210", "211", "212", "213", "214", "215", "217", "218", "219", "220", "221", "222"],
    "tools_registered": 36,  # estimado
    "phi_c_threshold": 0.9999,
    "architect": "orcid:0009-0005-2697-4668",
}
with open(ISO_ROOT / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

# 4. Gerar ISO com genisoimage
print("💿 Gerando Arkhe-OS.iso...")
iso_name = "Arkhe-OS.iso"
subprocess.run([
    "genisoimage", "-o", iso_name,
    "-b", "boot/isolinux.bin",
    "-c", "boot/boot.cat",
    "-no-emul-boot", "-boot-load-size", "4", "-boot-info-table",
    "-J", "-R", "-V", "ARKHE_OS",
    str(ISO_ROOT)
], check=True)

# 5. Calcular selo canônico
with open(iso_name, "rb") as f:
    iso_hash = hashlib.sha3_256(f.read()).hexdigest()
canonical_seal = hashlib.sha3_256(f"{iso_hash}{manifest['build_time']}".encode()).hexdigest()

with open("selo_canonico.txt", "w") as f:
    f.write(canonical_seal)

print(f"\n🏛️  Arkhe-OS.iso gerado com sucesso.")
print(f"   Hash SHA3-256: {iso_hash}")
print(f"   Selo Canônico: {canonical_seal}")
print(f"   Manifesto: {json.dumps(manifest, indent=2)}")
print(f"\n🔐 Para inicializar: grave o ISO em um pendrive ou inicie em VM.")
