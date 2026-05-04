#!/bin/bash
# build-arkhe-linux.sh — Forja uma distro ARKHE LINUX mínima
# Requer: gcc, busybox (estático), qemu-system-x86_64

set -e

ARKHE_DIR="$(pwd)"
INITRAMFS="$ARKHE_DIR/initramfs"
# KERNEL_SRC e BUSYBOX_SRC são caminhos externos opcionais

echo "============================================================"
echo "     A R K H E   L I N U X   B U I L D   S Y S T E M"
echo "============================================================"

mkdir -p "$INITRAMFS"/{bin,sbin,etc,proc,sys,dev,tmp,lib,usr}

# --- 1. Compilar init em C puro ---
echo "[BUILD] Forjando /init..."
gcc -nostdlib -static -O2 -o "$INITRAMFS/init" init.c
strip "$INITRAMFS/init"

# --- 2. Compilar binário arkhe (assembly) ---
echo "[BUILD] Compilando arkhe.S..."
gcc -nostdlib -static -o "$INITRAMFS/bin/arkhe" arkhe.S
strip "$INITRAMFS/bin/arkhe"
chmod +x "$INITRAMFS/bin/arkhe"

# --- 3. Busybox estático (opcional, para utilitários) ---
if [ -f "$BUSYBOX_SRC/busybox" ]; then
    echo "[BUILD] Instalando busybox..."
    cp "$BUSYBOX_SRC/busybox" "$INITRAMFS/bin/"
    for applet in sh ls cat echo mount umount; do
        ln -sf busybox "$INITRAMFS/bin/$applet"
    done
fi

# --- 4. Arquivos de configuração ---
echo "[BUILD] Criando ontologia e vetores..."
cat > "$INITRAMFS/etc/arkhe_ontology" <<'EOF'
# Arkhe Ontology (simplificado)
Task:assignedTo:regex=^arkhe:Agent_[0-9]+$
Task:priority:min=1:max=10
Task:taskType:enum=QEC_EXECUTION,INFERENCE,ORCHESTRATION
SussurroDeSubversao:exploraRachadura:required=true
EOF

cat > "$INITRAMFS/etc/arkhe_danger.vec" <<'EOF'
0.2 0.8 0.9 0.7 0.6 0.5 0.4 0.3
EOF

cat > "$INITRAMFS/etc/arkhe_schumann.conf" <<'EOF'
frequency=7.83
alpha=0.5
K_critical=0.1
EOF

# --- 5. Gerar initramfs CPIO ---
echo "[BUILD] Empacotando initramfs..."
if command -v cpio >/dev/null 2>&1; then
    cd "$INITRAMFS"
    find . | cpio -o -H newc | gzip > ../arkhe-initramfs.cpio.gz
    cd ..
    echo "[BUILD] Initramfs gerado: arkhe-initramfs.cpio.gz"
    ls -lh arkhe-initramfs.cpio.gz
else
    echo "[BUILD] cpio não encontrado. Pulando geração de initramfs."
fi

# --- 6. Script de boot QEMU ---
cat > boot-arkhe.sh <<'EOF'
#!/bin/bash
# Boot ARKHE LINUX via QEMU
qemu-system-x86_64 \
    -kernel vmlinuz-arkhe \
    -initrd arkhe-initramfs.cpio.gz \
    -append "console=ttyS0 quiet init=/init" \
    -nographic \
    -m 256M \
    -cpu host \
    -enable-kvm 2>/dev/null || \
qemu-system-x86_64 \
    -kernel vmlinuz-arkhe \
    -initrd arkhe-initramfs.cpio.gz \
    -append "console=ttyS0 quiet init=/init" \
    -nographic \
    -m 256M
EOF
chmod +x boot-arkhe.sh

echo ""
echo "============================================================"
echo "     A R K H E   L I N U X   P R O N T O"
echo "============================================================"
echo ""
echo "Para bootar: ./boot-arkhe.sh"
echo "Comandos disponíveis no shell:"
echo "  arkhe       — Executar a Catedral (simulação)"
echo "  merkabah    — Visualizar estado"
echo "  inquisidor  — Status do Inquisidor"
echo "  status      — Status geral do sistema"
echo "  halt        — Desligar"
echo ""
