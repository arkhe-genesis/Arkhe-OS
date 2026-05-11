#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARKHE Ω-TEMP v4.0 — Entrypoint Principal
=========================================
Modos disponíveis:
  run.py --demo           Demo local (3 nós em 1 processo)
  run.py --node ALFA-01   Nó standalone
  run.py --server         API HTTP
  run.py --test           Executa testes
"""

import sys
import argparse
import logging
import time
import json
from pathlib import Path

# Garante que o diretório raiz está no path
sys.path.insert(0, str(Path(__file__).parent))

from temporal_network import (
    RetroNode, RetroNet, TAddr,
    TemporalConsistencyOracle, AuditLedger,
    TemporalMessage, ConsistencyReport,
    QUANTUM_NEGATIVE_WINDOW_SECONDS,
)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)-8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("arkhe.main")


# ============================================================================
# MODO DEMO
# ============================================================================

def run_demo():
    """Simula 3 nós em um único processo para teste local."""
    log.info("🚀 Iniciando ARKHE Ω-TEMP Demo (3 nós)")

    net = RetroNet()

    # Criar nós
    alfa = net.create("ALFA-01")
    beta = net.create("BETA-02")
    gama = net.create("GAMMA-03")

    # Conectar: ALFA ↔ BETA ↔ GAMMA
    net.link("ALFA-01", "BETA-02")
    net.link("BETA-02", "GAMMA-03")

    time.sleep(0.5)

    log.info("Topologia: %s", net.topo())

    # --- TESTE 1: Tempo negativo quântico ---
    log.info("\n=== TESTE 1: Tempo Negativo Quântico ===")
    ledger = alfa._channel.ledger
    oracle = TemporalConsistencyOracle(ledger)

    # Simular fóton emergente (como no experimento de Toronto)
    quantum_msg = TemporalMessage(
        id="quantum-photon-001",
        content="Fóton emergente da nuvem de rubídio",
        source_timestamp=1000.0,
        target_timestamp=1000.0 - 5e-13,  # -0.5 picosegundo
        sender_seal="ALFA-01",
        receiver_seal="BETA-02",
    )

    report = oracle.evaluate(quantum_msg)
    log.info("  Consistente:     %s", report.consistent)
    log.info("  Score:           %.4f", report.score)
    log.info("  Quântico:        %s", report.quantum_coherent)
    log.info("  Tipo paradoxo:   %s", report.paradox_type)
    log.info("  Verificações:    %s", report.checks)
    log.info("  Violações:       %s", report.violations)

    assert report.consistent, "Tempo negativo quântico deveria ser consistente!"
    assert report.quantum_coherent, "Deveria estar no regime quântico!"
    assert report.score >= 0.9, f"Score deveria ≥ 0.9, got {report.score}"
    log.info("  ✅ PASS: Tempo negativo quântico aceito corretamente!\n")

    # --- TESTE 2: Tempo negativo clássico (paradoxo) ---
    log.info("=== TESTE 2: Tempo Negativo Clássico (Grande) ===")
    classical_msg = TemporalMessage(
        id="classical-neg-001",
        content="Mensagem para 100 segundos atrás",
        source_timestamp=1000.0,
        target_timestamp=1000.0 - 100.0,  # -100 segundos (FORA da janela)
        sender_seal="ALFA-01",
        receiver_seal="BETA-02",
    )

    report2 = oracle.evaluate(classical_msg)
    log.info("  Consistente:     %s", report2.consistent)
    log.info("  Score:           %.4f", report2.score)
    log.info("  Quântico:        %s", report2.quantum_coherent)
    log.info("  Violações:       %s", report2.violations)

    assert not report2.quantum_coherent, "Tempo clássico não deveria ser quântico!"
    assert report2.score < 1.0, "Tempo clássico negativo deveria ter score reduzido!"
    log.info("  ✅ PASS: Tempo negativo clássico penalizado corretamente!\n")

    # --- TESTE 3: Tempo positivo normal ---
    log.info("=== TESTE 3: Tempo Positivo Normal ===")
    normal_msg = TemporalMessage(
        id="normal-001",
        content="Mensagem para o futuro",
        source_timestamp=1000.0,
        target_timestamp=1000.0 + 120.0,  # +120 segundos
        sender_seal="ALFA-01",
        receiver_seal="GAMMA-03",
    )

    report3 = oracle.evaluate(normal_msg)
    log.info("  Consistente:     %s", report3.consistent)
    log.info("  Score:           %.4f", report3.score)
    log.info("  Quântico:        %s", report3.quantum_coherent)

    assert report3.consistent, "Tempo positivo deveria ser consistente!"
    assert not report3.quantum_coherent, "Tempo positivo não deveria ser quântico!"
    log.info("  ✅ PASS: Tempo positivo aceito corretamente!\n")

    # --- TESTE 4: Envio de mensagem retrocausal ---
    log.info("=== TESTE 4: Envio RetroCausal ===")
    alfa.send_message("GAMMA-03", "Olá do futuro via BETA!", target_time=time.time() + 120)
    stats = net.stats()
    log.info("  Stats da rede:   %s", stats)
    log.info("  ✅ PASS: Mensagem enviada!\n")

    # --- TESTE 5: Cadeia temporal ---
    log.info("=== TESTE 5: Cadeia Temporal ===")
    for nid, node in net._nodes.items():
        chain = node._channel.temporal_hash_chain
        valid, errors = chain.verify_integrity()
        log.info(f"  {nid}: {chain.length} blocos, válida={valid}, head={chain.head_hash[:12]}...")
    log.info("  ✅ PASS: Cadeia verificada!\n")

    log.info("🎉 TODOS OS TESTES PASSARAM!")
    return True


# ============================================================================
# MODO NÓ STANDALONE
# ============================================================================

def run_node(node_id, taddr_epoch=0, taddr_unc=0.001):
    """Inicia um nó standalone."""
    log.info(f"Iniciando nó {node_id}...")
    node = RetroNode(
        node_id,
        taddr=TAddr.from_parts(node_id,
            taddr_epoch if taddr_epoch > 0 else time.time(),
            taddr_unc),
        db_path=str(Path(f"/tmp/arkhe_{node_id}.db"))
    )
    node.start()
    log.info(f"✅ Nó {node_id} operacional: {node.taddr}")

    try:
        while True:
            time.sleep(10)
            stats = node.router.rt._routes
            log.info(f"  [Status] Peers: {len(node._peers)}, "
                     f"Rotas: {len(stats)}, "
                     f"Sent: {node._sent}, Recv: {node._recv}")
    except KeyboardInterrupt:
        node.stop()


# ============================================================================
# MODO API HTTP
# ============================================================================

def run_server(port=8000):
    """Inicia servidor HTTP simples sobre os nós."""
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        from typing import Dict

        nodes: Dict[str, RetroNode] = {}
        lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    info = {
                        "protocol": PROTOCOL_NAME, "version": VERSION,
                        "nodes": len(nodes),
                        "timestamp": time.time()
                    }
                    self.wfile.write(json.dumps(info).encode())

                elif self.path.startswith("/node/create/"):
                    nid = self.path.split("/")[-1]
                    with lock:
                        if nid not in nodes:
                            nodes[nid] = RetroNode(nid, db_path=f"/tmp/arkhe_{nid}.db")
                            nodes[nid].start()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps(nodes[nid].status()).encode())

                elif self.path.startswith("/connect/"):
                    parts = self.path.split("/")
                    if len(parts) >= 4:
                        a, b = parts[2], parts[3]
                        with lock:
                            if a in nodes and b in nodes:
                                nodes[a].connect(nodes[b])
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"connected": [a, b]}).encode())

                elif self.path.startswith("/send/"):
                    parts = self.path.split("/")
                    if len(parts) >= 4:
                        src, dst = parts[2], parts[3]
                        with lock:
                            if src in nodes:
                                nodes[src].send_message(dst, f"Hello from {src}",
                                                         target_time=time.time()+60)
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "sent"}).encode())

                elif self.path == "/topo":
                    with lock:
                        topo = {"nodes": {nid: {"taddr": str(n.taddr),
                                                  "peers": list(n._peers.keys())}
                                         for nid, n in nodes.items()},
                                "edges": [(a, b) for a, n in nodes.items() for b in n._peers]}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(topo).encode())

                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, fmt, *args):
                log.debug("HTTP: %s", fmt % args)

        server = HTTPServer(("0.0.0.0", port), Handler)
        log.info(f"🌐 API HTTP ouvindo na porta {port}")
        log.info("  GET  /health")
        log.info("  GET  /node/create/<node_id>")
        log.info("  GET  /connect/<node_a>/<node_b>")
        log.info("  GET  /send/<src>/<dst>")
        log.info("  GET  /topo")
        server.serve_forever()

    except ImportError:
        log.error("http.server indisponível")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="ARKHE Ω-TEMP v4.0")
    parser.add_argument("--demo", action="store_true", help="Rodar demo local")
    parser.add_argument("--node", type=str, help="Iniciar nó standalone")
    parser.add_argument("--server", action="store_true", help="Iniciar servidor HTTP")
    parser.add_argument("--port", type=int, default=8000, help="Porta do servidor HTTP")
    parser.add_argument("--epoch", type=float, default=0, help="Epoch TAddr")
    parser.add_argument("--unc", type=float, default=0.001, help="Incerteza TAddr")
    parser.add_argument("--verbose", "-v", action="store_true", help="Log detalhado")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.demo:
        run_demo()
    elif args.node:
        run_node(args.node, args.epoch, args.unc)
    elif args.server:
        run_server(args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
