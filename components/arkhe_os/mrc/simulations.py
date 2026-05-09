import numpy as np
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

from arkhe_os.network.mrc_transport import MRCTransportLayer, PlaneStatus
from arkhe_os.mrc.qhttp_bridge import QHTTPOverMRCBridge
from arkhe_os.mrc.roce_gateway import TemporalRoCEGateway, RoCEPacket, RoCEOpcode
from arkhe_os.mrc.load_balancer import CoherenceAwareLoadBalancer, NodeProfile
from arkhe_os.mrc.zk_privacy import MRCZKPrivacyLayer

def simulate_stargate_hypermesh_scenario(duration_steps: int = 80):
    workers = []
    for i in range(8):
        mrc = MRCTransportLayer(f"stargate_worker_{i}", num_planes=8)
        qhttp = QHTTPOverMRCBridge(f"stargate_worker_{i}", mrc)
        gateway = TemporalRoCEGateway(f"stargate_worker_{i}", qhttp)
        zk = MRCZKPrivacyLayer(f"stargate_worker_{i}", qhttp)
        workers.append({'mrc': mrc, 'qhttp': qhttp, 'gateway': gateway, 'zk': zk,
                       'node_id': f"stargate_worker_{i}"})

    node_profiles = [
        NodeProfile(f"stargate_worker_{i}", 200 + i*10, 128, 0.1 + i*0.05, 0.9 + i*0.01,
                   {"stargate_master": 3.0 + i*0.5}) for i in range(8)
    ]
    balancer = CoherenceAwareLoadBalancer(node_profiles, phi_threshold=0.5)

    history = {
        'step': [], 'avg_coherence': [], 'active_workers': [],
        'gradients_sent': [], 'zk_proofs': [], 'rebalance_events': [],
        'throughput_gbps': [], 'latency_ms': []
    }

    random.seed(42)
    np.random.seed(42)

    for step in range(duration_steps):
        if step == 20: workers[2]['mrc'].detect_failure(3, loss_rate=0.12)
        if step == 40: workers[5]['mrc'].detect_failure(1, loss_rate=0.10)
        if step == 60: workers[0]['mrc'].detect_failure(5, loss_rate=0.08)

        if step % 15 == 0 and step > 15:
            for w in workers:
                for pid in range(8):
                    if w['mrc'].planes[pid].status == PlaneStatus.RETIRED:
                        if random.random() < 0.4:
                            w['mrc'].send_probe(pid)
                w['mrc'].promote_recovered_planes()

        gradients_sent = 0
        zk_count = 0
        total_throughput = 0
        latencies = []

        for batch in range(4):
            gradient = np.random.randn(2048, 2048).astype(np.float32) * 0.001
            for _ in range(5):
                for w in workers:
                    balancer.update_coherence_measurement("stargate_master", w['node_id'],
                                                        w['mrc'].compute_transmission_coherence())

            alloc = balancer.allocate_tensor(gradient, "stargate_master")
            worker = workers[int(alloc['dest_node'].split('_')[-1])]
            proof = worker['zk'].prove_gradient_range(gradient, -0.01, 0.01)
            zk_count += 1

            roce_pkt = RoCEPacket(
                opcode=RoCEOpcode.WRITE, src_qp=batch, dest_qp=batch+100,
                r_key=0, addr=0, length=gradient.nbytes,
                payload=gradient[:50], psn=batch
            )
            result = worker['gateway'].send_roce_over_qhttp(roce_pkt, "stargate_master")

            if result['send_result']['status'] == 'SENT':
                gradients_sent += 1
                total_throughput += gradient.nbytes * 8 / 1e9
                latencies.append(result['translation_latency_ns'] / 1e6)

        rebalances = balancer.rebalance_cluster()
        coherences = [w['mrc'].compute_transmission_coherence() for w in workers]
        active = sum(1 for w in workers if w['mrc'].compute_transmission_coherence() > 0.5)

        history['step'].append(step)
        history['avg_coherence'].append(np.mean(coherences))
        history['active_workers'].append(active)
        history['gradients_sent'].append(gradients_sent)
        history['zk_proofs'].append(zk_count)
        history['rebalance_events'].append(len(rebalances))
        history['throughput_gbps'].append(total_throughput)
        history['latency_ms'].append(np.mean(latencies) if latencies else 0)

    return history

if __name__ == '__main__':
    history = simulate_stargate_hypermesh_scenario(80)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Quadrumvirato 257-260: Stargate Cluster na Hyper-Mesh', fontsize=14, fontweight='bold')

    ax1 = axes[0, 0]
    ax1.plot(history['step'], history['avg_coherence'], 'b-', linewidth=2, label='Φ_C média')
    ax1.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='Threshold')
    ax1.set_xlabel('Passo')
    ax1.set_ylabel('Coerência')
    ax1.set_title('Coerência Média do Cluster')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2 = axes[0, 1]
    ax2.plot(history['step'], history['gradients_sent'], 'g-', linewidth=2, label='Gradientes')
    ax2.plot(history['step'], history['zk_proofs'], 'orange', linewidth=2, label='ZK Proofs')
    ax2.set_xlabel('Passo')
    ax2.set_ylabel('Contagem')
    ax2.set_title('Gradientes e Proofs por Iteração')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[1, 0]
    ax3.plot(history['step'], history['throughput_gbps'], 'purple', linewidth=2)
    ax3.set_xlabel('Passo')
    ax3.set_ylabel('Throughput (Gb)')
    ax3.set_title('Throughput de Treinamento')
    ax3.grid(True, alpha=0.3)

    ax4 = axes[1, 1]
    ax4.plot(history['step'], history['latency_ms'], 'red', linewidth=2)
    ax4.set_xlabel('Passo')
    ax4.set_ylabel('Latência (ms)')
    ax4.set_title('Latência de Tradução RoCE→qhttp//')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    import os
    base = 'arkhe_os/output/substrates-257-260'
    os.makedirs(base, exist_ok=True)
    plt.savefig(f'{base}/simulation_stargate_hypermesh.png', dpi=150, bbox_inches='tight')
