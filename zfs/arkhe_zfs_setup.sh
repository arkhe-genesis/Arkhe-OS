#!/bin/sh
# ARKHE OS Substrato ∞: ZFS Dataset Setup
# Canon: ∞.Ω.∇+++.∞.zfs.setup
# Função: Criar estrutura de datasets ZFS para arquitetura híbrida
# Linguagem: Shell (FreeBSD sh)

set -e  # Exit on error

# Parâmetros configuráveis
ZPOOL="${ZPOOL:-zroot}"
BASE_DATASET="${ZPOOL}/arkhe"
SNAPSHOT_RETENTION_DAYS="${SNAPSHOT_RETENTION_DAYS:-30}"
COMPRESSION="${COMPRESSION:-lz4}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
    exit 1
}

# Verificar se zpool existe
if ! zpool list "$ZPOOL" >/dev/null 2>&1; then
    error "ZPool '$ZPOOL' not found. Create it first with: zpool create $ZPOOL ..."
fi

# Criar dataset base
log "Creating base dataset: $BASE_DATASET"
zfs create -o compression="$COMPRESSION" -o atime=off "$BASE_DATASET" || true

# Criar estrutura de datasets
log "Creating dataset structure..."

# Sistema base
zfs create "$BASE_DATASET/root" || true
zfs create "$BASE_DATASET/root/usr" || true
zfs create "$BASE_DATASET/root/var" || true

# Jails para agentes Arkhe
zfs create "$BASE_DATASET/jails" || true
zfs create -o quota=10G "$BASE_DATASET/jails/orchestrator" || true
zfs create -o quota=5G "$BASE_DATASET/jails/agent_zero" || true
zfs create -o quota=5G "$BASE_DATASET/jails/guardian" || true
zfs create -o quota=5G "$BASE_DATASET/jails/meta_learner" || true

# VMs bhyve
zfs create "$BASE_DATASET/vms" || true
zfs create -o volmode=dev -o compression=off "$BASE_DATASET/vms/linux_ai_01" || true
zfs create -o volmode=dev -o compression=off "$BASE_DATASET/vms/linux_ai_02" || true
zfs create -o volmode=dev -o compression=off "$BASE_DATASET/vms/linux_tools_01" || true

# Snapshots imutáveis do Cânone
zfs create "$BASE_DATASET/snapshots" || true
zfs create -o readonly=on "$BASE_DATASET/snapshots/canon" || true

# Audit logs imutáveis
zfs create "$BASE_DATASET/audit" || true
zfs create -o readonly=on -o compression=zstd "$BASE_DATASET/audit/temporal_chain" || true
zfs create -o readonly=on -o compression=zstd "$BASE_DATASET/audit/meta_audit" || true

# Configurar propriedades de segurança
log "Setting security properties..."
for dataset in $(zfs list -H -o name "$BASE_DATASET" | grep -v "/snapshots/canon$"); do
    zfs set aclmode=restricted "$dataset" || true
    zfs set aclinherit=restricted "$dataset" || true
done

# Configurar snapshots automáticos via cron
log "Configuring automated snapshots..."
cat > /usr/local/etc/cron.d/arkhe_zfs_snapshots <<EOF
# ARKHE ZFS Snapshot Cron Job
# Canon: ∞.Ω.∇+++.∞.zfs.cron

# Hourly snapshots for active datasets
0 * * * * root /usr/local/sbin/arkhe_zfs_snapshot hourly
# Daily snapshots with retention
0 2 * * * root /usr/local/sbin/arkhe_zfs_snapshot daily --retain $SNAPSHOT_RETENTION_DAYS
# Weekly canonical snapshots (immutable)
0 3 * * 0 root /usr/local/sbin/arkhe_zfs_snapshot weekly --immutable
EOF

chmod 644 /usr/local/etc/cron.d/arkhe_zfs_snapshots

# Criar script de snapshot helper
cat > /usr/local/sbin/arkhe_zfs_snapshot <<'SCRIPT'
#!/bin/sh
# ARKHE ZFS Snapshot Helper
set -e

TYPE="${1:-daily}"
RETAIN="${2:-7}"
IMMUTABLE=""

if [ "$TYPE" = "weekly" ] || [ "$3" = "--immutable" ]; then
    IMMUTABLE="-o readonly=on"
fi

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BASE_DATASET="zroot/arkhe"

for dataset in $(zfs list -H -o name "$BASE_DATASET" | grep -v "/snapshots/"); do
    # Skip if snapshot already exists
    if ! zfs list -t snapshot -H -o name "$dataset@$TYPE-$TIMESTAMP" >/dev/null 2>&1; then
        zfs snapshot $IMMUTABLE "$dataset@$TYPE-$TIMESTAMP"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Created snapshot: $dataset@$TYPE-$TIMESTAMP"
    fi
done

# Cleanup old snapshots if retention specified
if [ "$RETAIN" -gt 0 ]; then
    zfs list -t snapshot -H -o name "$BASE_DATASET" | grep "@$TYPE-" | \
        sort -t@ -k2 | head -n -$RETAIN | while read snapshot; do
        zfs destroy "$snapshot"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Destroyed old snapshot: $snapshot"
    done
fi
SCRIPT

chmod +x /usr/local/sbin/arkhe_zfs_snapshot

# Criar dataset para virtio-9p sharing
log "Creating 9p sharing dataset..."
zfs create "$BASE_DATASET/shared" || true
zfs set sharenfs=off "$BASE_DATASET/shared"
zfs set sharesmb=off "$BASE_DATASET/shared"

# Mount 9p export directory
mkdir -p /mnt/arkhe_9p_export
mount -t nullfs "$BASE_DATASET/shared" /mnt/arkhe_9p_export

log "ZFS setup completed successfully"
log "Datasets created:"
zfs list -r "$BASE_DATASET"

exit 0
