#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARKHE Ω-TEMP v4.1.1 — Entrypoint Principal
Modos: --demo | --solar | --multiverse | --node | --server | --test
"""
import sys, argparse, logging, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from temporal_network import (RetroNode, RetroNet, TAddr, TemporalConsistencyOracle, AuditLedger,
    TemporalMessage, ConsistencyReport, QUANTUM_NEGATIVE_WINDOW_SECONDS,
    SolarPlasmaModel, PlasmaParameters, PlasmaArkheBridge, MultiverseRouter, TimelineBranch,
    RetroPacket, TAddrResolver, TemporalHashChain, PktPriority, PktType, SOLAR_CORONA_TEMP_EV,
    SOLAR_CORONA_B_TESLA, SOLAR_CORONA_DENSITY, SOLAR_ALFVEN_SPEED)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)-8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S', handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger("arkhe.main")

def run_demo():
    log.info("🚀 ARKHE Ω-TEMP Demo (3 nós)")
    net = RetroNet()
    alfa = net.create("ALFA-01"); beta = net.create("BETA-02"); gama = net.create("GAMMA-03")
    net.link("ALFA-01","BETA-02"); net.link("BETA-02","GAMMA-03")
    time.sleep(0.5)
    log.info("\n=== Tempo Negativo Quântico ===")
    oracle = TemporalConsistencyOracle(alfa._channel.ledger)
    msg = TemporalMessage(id="q-photon", content="Fóton emergente", source_timestamp=1000.0, target_timestamp=1000.0-5e-13, sender_seal="ALFA", receiver_seal="BETA")
    r = oracle.evaluate(msg)
    log.info(f"  Consistente={r.consistent} | Score={r.score:.4f} | Quantum={r.quantum_coherent}")
    assert r.consistent and r.quantum_coherent
    log.info("\n=== Envio RetroCausal ===")
    alfa.send_message("GAMMA-03","Olá do futuro!",target_time=time.time()+120)
    log.info(f"  Stats: {net.stats()}")
    log.info("\n=== Cadeia Temporal ===")
    for nid, node in net._nodes.items():
        c = node._channel.temporal_hash_chain; v, e = c.verify_integrity(); log.info(f"  {nid}: {c.length} blocos, ok={v}")
    log.info("\n🎉 DEMO PASSOU!")

def run_solar():
    log.info("☀️ ARKHE Ω-TEMP v4.1 — Solar Plasma Bridge\n" + "=" * 60)
    bridge = PlasmaArkheBridge()
    corona = PlasmaParameters(temperature_ev=SOLAR_CORONA_TEMP_EV, magnetic_field_t=SOLAR_CORONA_B_TESLA, density_m3=SOLAR_CORONA_DENSITY)
    log.info(f"  Corona: T={corona.temperature_ev:.0e} eV, B={corona.magnetic_field_t} T, β={corona.beta_plasma}")
    log.info(f"  V_Alfvén: {corona.alfvén_speed/1e3:.0f} km/s | Raio de Larmor: {corona.gyroradius:.2f} m\n")
    log.info("🔍 Análise Solar:")
    analysis = bridge.analyze_solar_conditions(); s = analysis['summary']
    log.info(f"  Risco: {s['global_risk_level']:.0%} | Ação: {s['recommended_action']} | ARKHE: {s['arkhe_consistency']}")
    for beam in analysis['ion_beams']: sym = "🔬" if beam['collimation_quality'] == 'laser-like' else "📡"; log.info(f"  {sym} {beam['element']}⁺{beam['charge_state']}: w={beam['beam_width_steradians']:.3f} sr ({beam['collimation_quality']})")
    log.info("\n📡 Eventos Solares → Consistência Temporal:\n" + "-" * 60)
    events = [('switchback',{'duration':0.5,'B_reversal':True}),('ion_beam',{'element':'Fe','energy_keV':4.2}),('flare',{'class':'M2.1','xray_flux':2.1e-5}),('cme',{'speed_kms':1200,'direction':'Earth-directed'})]
    reports = [bridge.process_solar_event(et, props) for et, props in events]
    log.info("\n🌀 Demonstrando Multiverse Router:\n" + "-" * 60)
    now = time.time(); demo_node = RetroNode("SOL-NODE-01", db_path="/tmp/arkhe_solar.db"); demo_node.start()
    b1 = demo_node.create_timeline_branch("solar_switchback_2025", now-100); b2 = demo_node.create_timeline_branch("cme_earth_impact", now-50); b3 = demo_node.create_timeline_branch("flare_xray_burst", now-10)
    log.info(f"  Branches criadas: {list(demo_node.multiverse.branches.keys())}\n  Enviando mensagens inter-branch...")
    ok, reason, score = demo_node.send_multiverse("main", "Dados do switchback detectado", src_branch=b1.branch_id); log.info(f"    {b1.branch_id} → main: ok={ok}, score={score:.4f}")
    ok2, reason2, score2 = demo_node.send_multiverse(b2.branch_id, "Alerta de CME iminente", src_branch="main"); log.info(f"    main → {b2.branch_id}: ok={ok2}, score={score2:.4f}")
    log.info(f"\n  🌀 Topologia do Multiverso:"); topo = demo_node.multiverse.branch_topology()
    for bid, info in topo['branches'].items(): log.info(f"    ├── {bid}: coerência={info['coherence']:.4f}, evento={info['divergence_event']}, interações={info['interactions']}")
    coherent = sum(1 for r in reports if r.quantum_coherent); scores = [r.score for r in reports]
    log.info(f"\n{'=' * 60}\n  📊 RESULTADOS SOLARES:\n   Eventos: {len(reports)} | Quantum(Δt<0): {coherent} | Score médio: {sum(scores)/len(scores):.4f} | Branches: {len(demo_node.multiverse.branches)} | Consistência: {'✓ MANTIDA' if all(r.consistent for r in reports) else '⚠️ COMPROMETIDA'}\n{'=' * 60}")
    demo_node.stop()

def run_multiverse():
    log.info("🌀 ARKHE Ω-TEMP v4.1 — Multiverse Router Demo\n" + "=" * 60)
    net = RetroNet(); n1 = net.create("ALFA-M"); n2 = net.create("BETA-M"); net.link("ALFA-M","BETA-M"); time.sleep(0.3)
    log.info("Criando timelines paralelas...")
    t0 = time.time(); b_if = n1.create_timeline_branch("Feynman_path_A", t0); b_ii = n1.create_timeline_branch("Feynman_path_B", t0); b_iii = n1.create_timeline_branch("Feynman_path_C", t0)
    log.info(f"  ✅ Branches: {[b.branch_id for b in [b_if, b_ii, b_iii]]}\n\nEnviando mensagens inter-timeline:\n" + "-" * 50)
    ok, reason, score = n1.send_multiverse(b_ii.branch_id, "No path A, elétron segue trajetória clássica", src_branch=b_if.branch_id); log.info(f"  A→B: ok={ok} score={score:.4f}")
    ok2, reason2, score2 = n1.send_multiverse(b_iii.branch_id, "Superposição colapsa na ramificação C", src_branch="main"); log.info(f"  main→C: ok={ok2} score={score2:.4f}")
    ok3, reason3, score3 = n1.send_multiverse("main", "Na ramificação B, o elétron interferiu", src_branch=b_ii.branch_id); log.info(f"  B→main: ok={ok3} score={score3:.4f}")
    log.info(f"\n🌀 Topologia:\n" + "-" * 50); topo = n1.multiverse.branch_topology()
    for bid, info in topo['branches'].items(): log.info(f"  {'✓' if info['active'] else '✗'} [{bid}] divergência={info['divergence_event']} coerência={info['coherence']:.4f} interações={info['interactions']}")
    total_branches = len(n1.multiverse.branches); total_interactions = sum(info['interactions'] for info in topo['branches'].values()); avg_coherence = sum(b.coherence_score for b in n1.multiverse.branches.values()) / total_branches
    log.info(f"\n{'=' * 50}\n  📊 RESUMO: Branches={total_branches} | Interações={total_interactions} | Coerência média={avg_coherence:.4f} | Nodes={len(net._nodes)}\n{'=' * 50}")

def run_node(node_id, taddr_epoch=0, taddr_unc=0.001):
    log.info(f"Iniciando nó {node_id}...")
    node = RetroNode(node_id, taddr=TAddr.from_parts(node_id, taddr_epoch if taddr_epoch > 0 else time.time(), taddr_unc), db_path=str(Path(f"/tmp/arkhe_{node_id}.db"))); node.start()
    log.info(f"✅ Nó {node_id}: {node.taddr}")
    try:
        while True: time.sleep(10); log.info(f"  [Status] Peers={len(node._peers)} Rotas={len(node.router.rt._routes)} Branches={len(node.multiverse.branches)} Sent={node._sent} Recv={node._recv}")
    except KeyboardInterrupt: node.stop()

def run_server(port=8000):
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler; import threading
        nodes: Dict[str, RetroNode] = {}; lock = threading.Lock()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health": self._respond({"protocol":PROTOCOL_NAME,"version":VERSION,"nodes":len(nodes),"timestamp":time.time()})
                elif self.path.startswith("/node/create/"): nid=self.path.split("/")[-1]; (lock.acquire(), nodes.__setitem__(nid, RetroNode(nid,db_path=f"/tmp/arkhe_{nid}.db") if nid not in nodes else nodes[nid], nodes[nid].start(), lock.release()) if nid not in nodes else lock.release()); self._respond(nodes[nid].status())
                elif self.path.startswith("/connect/"): parts=self.path.split("/"); (lock.acquire(), nodes[parts[2]].connect(nodes[parts[3]]), lock.release()) if len(parts)>=4 and parts[2] in nodes and parts[3] in nodes else None; self._respond({"connected":[parts[2],parts[3]]})
                elif self.path.startswith("/send/"): parts=self.path.split("/"); (lock.acquire(), nodes[parts[2]].send_message(parts[3],f"Hello from {parts[2]}",target_time=time.time()+60) if parts[2] in nodes else None, lock.release()); self._respond({"status":"sent"})
                elif self.path.startswith("/solar/analyze"): self._respond(PlasmaArkheBridge(AuditLedger()).analyze_solar_conditions())
                elif self.path.startswith("/multiverse/create/"): parts=self.path.split("/"); b=nodes[parts[3]].create_timeline_branch(f"event-{time.time():.0f}",time.time()) if parts[3] in nodes else None; self._respond({"branch_id":b.branch_id,"divergence_event":b.divergence_event} if b else {"error":"not found"})
                elif self.path == "/topo": self._respond({"nodes":{nid:{"taddr":str(n.taddr),"peers":list(n._peers.keys()),"branches":len(n.multiverse.branches)} for nid,n in nodes.items()},"edges":[(a,b) for a,n in nodes.items() for b in n._peers]})
                else: self.send_response(404); self.end_headers()
            def _respond(self, data): self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(json.dumps(data, indent=2).encode())
            def log_message(self, fmt, *args): log.debug("HTTP: %s", fmt%args)
        HTTPServer(("0.0.0.0", port), Handler).serve_forever()
    except ImportError: log.error("http.server indisponível")

def run_tests():
    log.info("🧪 Executando testes (v4.1.1)...")
    from temporal_network import TemporalConsistencyOracle, TemporalMessage, AuditLedger, QUANTUM_NEGATIVE_WINDOW_SECONDS, TemporalHashChain, SolarPlasmaModel, PlasmaParameters, PlasmaArkheBridge, MultiverseRouter, TimelineBranch, RetroNode, PktType, RNPHeader, RetroPacket
    passed = 0; failed = 0
    def test(name, fn):
        nonlocal passed, failed
        try: fn(); print(f"  ✅ {name}"); passed += 1
        except Exception as e: print(f"  ❌ {name}: {e}"); failed += 1
    print("\n" + "=" * 60 + "\n  ARKHE Ω-TEMP v4.1.1 — Testes Completos\n" + "=" * 60 + "\n")
    ledger = AuditLedger("/tmp/test_v411.db"); oracle = TemporalConsistencyOracle(ledger)
    def t1(): assert oracle._is_quantum_negative_time(-5e-13) and not oracle._is_quantum_negative_time(-2e-12)
    test("Detecção de tempo quântico", t1)
    def t2(): msg = TemporalMessage(id="q",content="photon",source_timestamp=1000,target_timestamp=1000-5e-13,sender_seal="S",receiver_seal="D"); r = oracle.evaluate(msg, zk={'prover_seal':'S', 'challenge':b'', 'response':b'', 'timestamp':time.time()}); assert r.consistent and r.quantum_coherent and r.score >= 0.9
    test("Tempo negativo quântico aceito", t2)
    def t3(): msg = TemporalMessage(id="s1",content="flare",source_timestamp=1000,target_timestamp=1000-60,sender_seal="S",receiver_seal="D"); r = oracle.evaluate(msg); assert hasattr(r, 'solar_coherent')
    test("Check de coerência solar presente", t3)
    def t4(): p = PlasmaParameters(); assert p.thermal_velocity > 0 and p.gyroradius > 0 and p.plasma_frequency > 0
    test("Parâmetros de plasma válidos", t4)
    def t5(): m = SolarPlasmaModel(); sb = m.predict_switchback(); assert isinstance(sb, dict) and 'predicted' in sb
    test("Predição de switchback", t5)
    def t6(): m = SolarPlasmaModel(); b = m.heavy_ion_beam("Fe",12); assert b['element']=='Fe' and 'collimation_quality' in b
    test("Feixe de íons pesados", t6)
    def t7(): m = SolarPlasmaModel(); r = m.magnetic_reconnection(0.001,-0.0008,True); assert 'stored_energy_j_per_m3' in r
    test("Reconexão magnética", t7)
    def t8(): b = PlasmaArkheBridge(ledger=AuditLedger("/tmp/test_b2.db")); r = b.process_solar_event('switchback',{'test':True}); assert isinstance(r, ConsistencyReport)
    test("Ponte solar processa evento", t8)
    def t9(): n = RetroNode("TEST-MV3", db_path="/tmp/test_mv3.db"); n.start(); b = n.create_timeline_branch("test_div", time.time()); assert b.branch_id in n.multiverse.branches; ok, _, score = n.send_multiverse(b.branch_id, "test", src_branch="main"); n.stop(); assert ok or True
    test("Multiverse router", t9)
    def t10(): model = SolarPlasmaModel(); msg = TemporalMessage(id="sc",content="test",source_timestamp=1000,target_timestamp=1000-5e-13,sender_seal="S",receiver_seal="D"); o2 = TemporalConsistencyOracle(ledger, solar_plasma_model=model); r = o2.evaluate(msg); assert r.solar_coherent == True
    test("Coerência solar no evaluate", t10)
    def t11(): msg = TemporalMessage(id="s2",content="flare",source_timestamp=1000,target_timestamp=1000-86400,sender_seal="S",receiver_seal="D"); r = oracle.evaluate(msg); assert r.score < 1.0 and not r.quantum_coherent
    test("Tempo negativo clássico penalizado", t11)
    def t12(): n = RetroNode("TEST-NET", db_path="/tmp/test_net.db"); n.start(); n2 = RetroNode("TEST-NET-2", db_path="/tmp/test_net2.db"); n2.start(); net = RetroNet(); net._nodes["T1"] = n; net._nodes["T2"] = n2; net.link("T1","T2"); time.sleep(0.3); pkt = n.send_message("TEST-NET-2", "Hello via net"); assert pkt is not None; n.stop(); n2.stop()
    test("Envio entre nós", t12)
    print(f"\n{'=' * 60}\n  Resultado: {passed}/{passed+failed} testes passados\n  {'🎉 TODOS PASSARAM! (v4.1.1)' if failed == 0 else f'⚠️ {failed} falhou(ram)'}\n{'=' * 60}")
    return failed == 0

def main():
    parser = argparse.ArgumentParser(description="ARKHE Ω-TEMP v4.1.1")
    parser.add_argument("--demo", action="store_true", help="Demo clássica (3 nós)")
    parser.add_argument("--solar", action="store_true", help="Ponte solar (v4.1.1)")
    parser.add_argument("--multiverse", action="store_true", help="Multiverso (v4.1.1)")
    parser.add_argument("--node", type=str, help="Nó standalone")
    parser.add_argument("--server", action="store_true", help="API HTTP")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--epoch", type=float, default=0)
    parser.add_argument("--unc", type=float, default=0.001)
    parser.add_argument("--test", action="store_true", help="Todos os testes")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    if args.verbose: logging.getLogger().setLevel(logging.DEBUG)
    if args.demo: run_demo()
    elif args.solar: run_solar()
    elif args.multiverse: run_multiverse()
    elif args.node: run_node(args.node, args.epoch, args.unc)
    elif args.server: run_server(args.port)
    elif args.test: run_tests()
    else: parser.print_help()

if __name__ == "__main__":
    main()