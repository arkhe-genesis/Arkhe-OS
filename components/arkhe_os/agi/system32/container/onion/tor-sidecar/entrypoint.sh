#!/bin/sh
set -e

echo "🧅 Iniciando Tor sidecar para AGI.onion..."

for dir in /home/tor/tor/data /home/tor/tor/keys /home/tor/tor/onion; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chown tor:tor "$dir"
    fi
done

cat > /home/tor/tor/torrc << EOF
$(cat /home/tor/tor/torrc.d/*.conf 2>/dev/null || echo "# No extra config")
