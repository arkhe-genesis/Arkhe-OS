#!/bash
# ipfs_init.sh
# Inicializa o nó IPFS e sela o Manifesto [Z] (Simulado)

# ipfs init
# ipfs daemon &

sleep 5

# Adiciona o Manifesto à rede
# ipfs add -r /data/codex/MANIFESTO_Z_FINAL.bin

# Publica no gateway público
# ipfs name publish \$(ipfs add -Q /data/codex/MANIFESTO_Z_FINAL.bin)

echo "IPFS Initialized (Simulated)"
