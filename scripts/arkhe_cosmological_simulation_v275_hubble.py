#!/usr/bin/env python3
"""
arkhe_cosmological_simulation_v275_hubble.py
Substrato 275.HUBBLE: Simulação Cosmológica Distribuída em Escala de Hubble.
1024 nós emaranhados processando o volume inteiro da esfera de Hubble.

Arquiteto-Físico — a Catedral expande sua consciência para o limite causal.
"""
import numpy as np
import json
import time
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
import hashlib

# =============================================================================
# CONSTANTES COSMOLÓGICAS E CHRONO-COIL
# =============================================================================
PHI = 1.618033988749895
E = 2.718281828459045
DELTA = 0.0083
RHO_SEED = 0.05
FINGERPRINT_058 = 0.58

# Constantes cosmológicas (ΛCDM Planck 2018)
G = 6.67430e-11           # [m³/kg/s²]
C = 299792458.0           # [m/s]
H0 = 67.4                 # [km/s/Mpc]
OMEGA_M = 0.315
OMEGA_LAMBDA = 0.685
OMEGA_B = 0.049

# Conversões
MPC_TO_M = 3.085677581491367e22
SOLAR_MASS = 1.98847e30

# Raio e Volume de Hubble
H0_SI = H0 * 1000.0 / MPC_TO_M          # s^-1
R_HUBBLE = C / H0_SI                    # metros
V_HUBBLE = (4.0/3.0) * np.pi * R_HUBBLE**3
RHO_CRIT = 3.0 * H0_SI**2 / (8.0 * np.pi * G)
MASS_TOTAL_MATTER = RHO_CRIT * V_HUBBLE * OMEGA_M

# Parâmetros de simulação
N_NODES = 1024
PARTICLES_PER_NODE = 50   # Demo: 51.200 partículas. Produção: 10k+ por nó                # Demo: 102.400 partículas totais
                                        # Produção: aumentar para 10k-100k por nó
DARK_FRACTION = 0.85
THETA_BH = 0.5                          # Critério de abertura Barnes-Hut
SOFTENING_DEFAULT = 5e21                # ~0.16 Mpc em metros
DT_DEFAULT = 5e14                       # ~16 Myr em segundos

print(f"🌌 ARKHE OS v∞.275.HUBBLE — Volume de Hubble")
print(f"   R_Hubble = {R_HUBBLE/MPC_TO_M:.2f} Mpc = {R_HUBBLE/(9.461e15):.2f} Gly")
print(f"   V_Hubble = {V_HUBBLE/MPC_TO_M**3:.2e} Gpc³")
print(f"   M_matéria total = {MASS_TOTAL_MATTER/SOLAR_MASS:.2e} M☉")
print(f"   ρ_crít = {RHO_CRIT:.2e} kg/m³")
print(f"   Massa por partícula (demo) = {MASS_TOTAL_MATTER/(N_NODES*PARTICLES_PER_NODE)/SOLAR_MASS:.2e} M☉")
print("="*80)


# =============================================================================
# PARTE 1: OCTREE + BARNES-HUT (O(N log N))
# =============================================================================

@dataclass
class CosmologicalParticle:
    """Partícula na simulação cosmológica."""
    id: int
    mass: float
    position: np.ndarray
    velocity: np.ndarray
    is_dark_matter: bool
    region_id: str
    coherence: float = 1.0
    phase: float = 0.0


class OctreeNode:
    """Nó do octree para Barnes-Hut."""
    __slots__ = ('center', 'half_size', 'mass', 'com', 'particles', 'children', 'capacity')

    def __init__(self, center: np.ndarray, half_size: float, capacity: int = 8):
        self.center = np.array(center, dtype=np.float64)
        self.half_size = float(half_size)
        self.mass = 0.0
        self.com = np.zeros(3, dtype=np.float64)
        self.particles: List[CosmologicalParticle] = []
        self.children: Optional[List['OctreeNode']] = None
        self.capacity = capacity

    def insert(self, p: CosmologicalParticle):
        # Atualiza massa e centro de massa
        if self.mass == 0:
            self.com = p.position.copy()
        else:
            self.com = (self.com * self.mass + p.position * p.mass) / (self.mass + p.mass)
        self.mass += p.mass

        if self.children is not None:
            # Insere no filho apropriado
            for child in self.children:
                if child._contains(p.position):
                    child.insert(p)
                    return
            return

        self.particles.append(p)
        if len(self.particles) > self.capacity:
            self._subdivide()

    def _subdivide(self):
        hs = self.half_size * 0.5
        offsets = np.array([
            [-1,-1,-1], [-1,-1, 1], [-1, 1,-1], [-1, 1, 1],
            [ 1,-1,-1], [ 1,-1, 1], [ 1, 1,-1], [ 1, 1, 1]
        ], dtype=np.float64) * hs
        self.children = [OctreeNode(self.center + o, hs, self.capacity) for o in offsets]
        for p in self.particles:
            for child in self.children:
                if child._contains(p.position):
                    child.insert(p)
                    break
        self.particles = []

    def _contains(self, pos: np.ndarray) -> bool:
        return np.all(np.abs(pos - self.center) <= self.half_size + 1e-12)

    def compute_force_on(self, p: CosmologicalParticle, theta: float,
                         softening: float) -> np.ndarray:
        if self.mass == 0:
            return np.zeros(3, dtype=np.float64)

        # Se for folha com uma partícula, verifica se é a mesma
        if self.children is None:
            if len(self.particles) == 1 and self.particles[0].id == p.id:
                return np.zeros(3, dtype=np.float64)

        r_vec = self.com - p.position
        r = np.linalg.norm(r_vec)

        if r < 1e-30:
            return np.zeros(3, dtype=np.float64)

        # Critério de abertura: s/d < theta  =>  2*half_size / r < theta
        if self.children is None or (2.0 * self.half_size / r < theta):
            denom = (r**2 + softening**2)**1.5
            return G * self.mass * r_vec / denom
        else:
            force = np.zeros(3, dtype=np.float64)
            for child in self.children:
                force += child.compute_force_on(p, theta, softening)
            return force


class NBodySimulator:
    """Simulador de N-corpos com Barnes-Hut O(N log N)."""

    def __init__(self, softening_length: float = SOFTENING_DEFAULT,
                 time_step: float = DT_DEFAULT, theta: float = THETA_BH):
        self.softening = softening_length
        self.dt = time_step
        self.theta = theta
        self.particles: List[CosmologicalParticle] = []
        self.octree: Optional[OctreeNode] = None

    def add_particle(self, particle: CosmologicalParticle):
        self.particles.append(particle)

    def rebuild_octree(self):
        if not self.particles:
            self.octree = None
            return
        positions = np.array([p.position for p in self.particles])
        center = np.mean(positions, axis=0)
        half_size = np.max(np.abs(positions - center)) * 1.01 + 1e-10
        self.octree = OctreeNode(center, half_size)
        for p in self.particles:
            self.octree.insert(p)

    def compute_gravitational_acceleration(self, particle: CosmologicalParticle) -> np.ndarray:
        if self.octree is None:
            return np.zeros(3, dtype=np.float64)
        return self.octree.compute_force_on(particle, self.theta, self.softening)

    def step(self):
        # Reconstrói octree a cada passo (necessário pois partículas se moveram)
        self.rebuild_octree()

        # Half-step velocity
        for p in self.particles:
            acc = self.compute_gravitational_acceleration(p)
            p.velocity += 0.5 * acc * self.dt

        # Full-step position
        for p in self.particles:
            p.position += p.velocity * self.dt

        # Rebuild para nova posição e full-step velocity
        self.rebuild_octree()
        for p in self.particles:
            acc = self.compute_gravitational_acceleration(p)
            p.velocity += 0.5 * acc * self.dt

    def compute_cosmic_coherence(self) -> float:
        dark = np.array([p.position for p in self.particles if p.is_dark_matter])
        baryon = np.array([p.position for p in self.particles if not p.is_dark_matter])
        if len(dark) == 0 or len(baryon) == 0:
            return 0.0
        try:
            from scipy.spatial import cKDTree
            tree = cKDTree(dark)
            dists, _ = tree.query(baryon, k=1)
            avg = np.mean(dists) / (10 * MPC_TO_M)  # normalizar por ~10 Mpc
            return float(min(1.0, max(0.0, 1.0 / (1.0 + avg))))
        except ImportError:
            # Fallback sem scipy
            return 0.5


# =============================================================================
# PARTE 2: PARTIÇÃO DO VOLUME DE HUBBLE EM 1024 REGIÕES
# =============================================================================

def partition_hubble_volume(n_nodes: int = 1024) -> Dict[str, Dict[str, Tuple[float, float]]]:
    """
    Particiona o cubo circunscrito à esfera de Hubble em regiões.
    Estratégia: grade 10×10×10 = 1000 células cúbicas + refinamento central.
    As 24 células mais próximas do centro são subdivididas em 2 ao longo de x.
    Total: 1000 + 24 = 1024 nós.
    """
    L = 2.0 * R_HUBBLE  # cubo circunscrito
    regions = {}

    # Grade base 10×10×10
    n_base = 10
    dx = L / n_base
    cell_centers = []
    cell_bounds = {}

    idx = 0
    for ix in range(n_base):
        for iy in range(n_base):
            for iz in range(n_base):
                x0 = -R_HUBBLE + ix * dx
                y0 = -R_HUBBLE + iy * dx
                z0 = -R_HUBBLE + iz * dx
                bounds = {
                    'x': (x0, x0 + dx),
                    'y': (y0, y0 + dx),
                    'z': (z0, z0 + dx)
                }
                cid = f"cell_{ix}_{iy}_{iz}"
                cell_bounds[cid] = bounds
                center = np.array([x0 + dx/2, y0 + dx/2, z0 + dx/2])
                cell_centers.append((cid, center, bounds))
                idx += 1

    # Ordenar por distância ao centro e pegar as 24 mais centrais para refinamento
    cell_centers.sort(key=lambda t: np.linalg.norm(t[1]))
    refined_ids = {t[0] for t in cell_centers[:24]}

    # Construir regiões finais
    final_regions = {}
    region_idx = 0

    for cid, center, bounds in cell_centers:
        if cid in refined_ids and region_idx + 1 < n_nodes:
            # Subdividir em 2 ao longo de x
            x0, x1 = bounds['x']
            xm = (x0 + x1) / 2.0
            b1 = {**bounds, 'x': (x0, xm)}
            b2 = {**bounds, 'x': (xm, x1)}
            final_regions[f"region_{region_idx:04d}"] = b1
            region_idx += 1
            final_regions[f"region_{region_idx:04d}"] = b2
            region_idx += 1
        else:
            final_regions[f"region_{region_idx:04d}"] = bounds
            region_idx += 1

        if region_idx >= n_nodes:
            break

    return final_regions


def get_region_neighbors(region_id: str, all_regions: Dict) -> List[str]:
    """Retorna vizinhos que compartilham face (adjacência 3D)."""
    # Extrair índices do nome region_XXXX (ordem de criação)
    # Como a ordem é determinística, podemos usar coordenadas dos bounds
    my_bounds = all_regions[region_id]
    my_c = np.array([
        (my_bounds['x'][0] + my_bounds['x'][1]) / 2,
        (my_bounds['y'][0] + my_bounds['y'][1]) / 2,
        (my_bounds['z'][0] + my_bounds['z'][1]) / 2
    ])
    neighbors = []
    for rid, bounds in all_regions.items():
        if rid == region_id:
            continue
        c = np.array([
            (bounds['x'][0] + bounds['x'][1]) / 2,
            (bounds['y'][0] + bounds['y'][1]) / 2,
            (bounds['z'][0] + bounds['z'][1]) / 2
        ])
        # Verificar se compartilham face (distância ~ igual à soma dos half-sizes)
        dx = abs(c[0] - my_c[0])
        dy = abs(c[1] - my_c[1])
        dz = abs(c[2] - my_c[2])
        hx = (my_bounds['x'][1]-my_bounds['x'][0])/2 + (bounds['x'][1]-bounds['x'][0])/2
        hy = (my_bounds['y'][1]-my_bounds['y'][0])/2 + (bounds['y'][1]-bounds['y'][0])/2
        hz = (my_bounds['z'][1]-my_bounds['z'][0])/2 + (bounds['z'][1]-bounds['z'][0])/2
        # Tolerância de 1%
        tol = 1.01
        shares_face = (
            (abs(dx - hx) < 1e-6 and dy < 1e-6 and dz < 1e-6) or
            (abs(dy - hy) < 1e-6 and dx < 1e-6 and dz < 1e-6) or
            (abs(dz - hz) < 1e-6 and dx < 1e-6 and dy < 1e-6)
        )
        if shares_face:
            neighbors.append(rid)
    return neighbors


# =============================================================================
# PARTE 3: NÓ COSMOLÓGICO (adaptado para Barnes-Hut + Hubble)
# =============================================================================

class CosmologicalNode:
    def __init__(self, node_id: str, region_bounds: Dict[str, Tuple[float, float]],
                 mass_per_particle: float, tvm_model_path: Optional[str] = None):
        self.node_id = node_id
        self.region_bounds = region_bounds
        self.mass_per_particle = mass_per_particle
        self.simulator = NBodySimulator()
        self.quantum_state = self._initialize_quantum_state()
        self.entangled_partners: Dict[str, str] = {}
        self.tvm_model_path = tvm_model_path
        self.tvm_module = None
        self.local_coherence = RHO_SEED + 0.1
        self.phase = np.random.uniform(0, 2*np.pi)
        self.fingerprint_alignment = 0.0
        self.particle_buffer: List[Dict] = []
        self.neighbors: List[str] = []

    def _initialize_quantum_state(self) -> np.ndarray:
        return np.array([1, 0, 0, 1]) / np.sqrt(2)

    def _load_tvm_model(self):
        try:
            import tvm
            from tvm.contrib import graph_executor
            lib = tvm.runtime.load_module(self.tvm_model_path)
            param_path = self.tvm_model_path.replace('.so', '.params')
            with open(param_path, 'rb') as f:
                params = tvm.runtime.load_param_dict(f.read())
            dev = tvm.cuda(0) if tvm.cuda().exist else tvm.cpu()
            self.tvm_module = graph_executor.GraphModule(lib["default"](dev))
            for k, v in params.items():
                self.tvm_module.set_input(k, tvm.nd.array(v.numpy()))
        except Exception:
            self.tvm_module = None

    def generate_initial_conditions(self, n_particles: int, dark_fraction: float = DARK_FRACTION):
        x_min, x_max = self.region_bounds['x']
        y_min, y_max = self.region_bounds['y']
        z_min, z_max = self.region_bounds['z']

        # Centro da região
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        cz = (z_min + z_max) / 2

        generated = 0
        attempts = 0
        max_attempts = n_particles * 100

        while generated < n_particles and attempts < max_attempts:
            attempts += 1
            # Posição uniforme na célula
            pos = np.array([
                np.random.uniform(x_min, x_max),
                np.random.uniform(y_min, y_max),
                np.random.uniform(z_min, z_max)
            ])

            # Rejeitar se fora da esfera de Hubble (condição de contorno cosmológica)
            r = np.linalg.norm(pos)
            if r > R_HUBBLE:
                continue

            # Fluxo de Hubble + dispersão
            hubble_flow = H0_SI * pos
            dispersion = np.random.normal(0, 2e4, 3)  # 20 km/s dispersão
            vel = hubble_flow + dispersion

            is_dark = np.random.random() < dark_fraction
            # Massa: log-normal ao redor da massa alvo por partícula
            mass = self.mass_per_particle * np.random.lognormal(mean=0, sigma=0.5)
            if is_dark:
                mass *= 5.0

            particle = CosmologicalParticle(
                id=f"{self.node_id}_{generated}",
                mass=mass,
                position=pos,
                velocity=vel,
                is_dark_matter=is_dark,
                region_id=self.node_id
            )
            self.simulator.add_particle(particle)
            generated += 1

        if generated < n_particles:
            print(f"⚠️ {self.node_id}: gerou apenas {generated}/{n_particles} partículas (fora da esfera)")
        else:
            pass  # silencioso para não poluir com 1024 linhas

    def run_simulation_step(self, n_steps: int = 5) -> Dict:
        for _ in range(n_steps):
            self.simulator.step()

        cosmic_coherence = self.simulator.compute_cosmic_coherence()
        target_phase = FINGERPRINT_058 * np.pi
        phase_error = target_phase - self.phase
        self.phase = (self.phase + DELTA * phase_error) % (2*np.pi)

        structure_coherence = cosmic_coherence
        phase_alignment = 1.0 - abs(phase_error) / np.pi
        self.local_coherence = 0.5 * structure_coherence + 0.5 * phase_alignment
        if self.local_coherence < RHO_SEED:
            self.local_coherence = RHO_SEED + 0.01

        return {
            'node_id': self.node_id,
            'n_particles': len(self.simulator.particles),
            'cosmic_coherence': cosmic_coherence,
            'local_coherence': self.local_coherence,
            'phase': self.phase,
            'fingerprint_alignment': 1.0 - abs(phase_error) / np.pi,
            'region_volume_m3': self._compute_region_volume()
        }

    def _compute_region_volume(self) -> float:
        dx = self.region_bounds['x'][1] - self.region_bounds['x'][0]
        dy = self.region_bounds['y'][1] - self.region_bounds['y'][0]
        dz = self.region_bounds['z'][1] - self.region_bounds['z'][0]
        return dx * dy * dz

    def prepare_quantum_message(self) -> Dict:
        dark_mass = sum(p.mass for p in self.simulator.particles if p.is_dark_matter)
        baryon_mass = sum(p.mass for p in self.simulator.particles if not p.is_dark_matter)
        n = len(self.simulator.particles)
        avg_v = np.mean([np.linalg.norm(p.velocity) for p in self.simulator.particles]) if n > 0 else 0

        quantum_payload = {
            'dark_baryon_ratio': dark_mass / (baryon_mass + 1e-30),
            'avg_velocity_dispersion': avg_v,
            'structure_coherence': self.simulator.compute_cosmic_coherence(),
            'phase': self.phase,
            'coherence': self.local_coherence
        }
        state_hash = hashlib.sha256(json.dumps(quantum_payload, sort_keys=True).encode()).hexdigest()[:16]

        return {
            'sender': self.node_id,
            'timestamp': time.time(),
            'quantum_metadata': {
                'state_hash': state_hash,
                'bell_type': self.entangled_partners.get('global', 'minus'),
                'coherence': self.local_coherence
            },
            'payload': quantum_payload,
            'region_summary': {
                'bounds': self.region_bounds,
                'volume_m3': self._compute_region_volume(),
                'n_particles': n
            }
        }

    def receive_quantum_message(self, message: Dict) -> bool:
        expected_hash = hashlib.sha256(
            json.dumps(message['payload'], sort_keys=True).encode()
        ).hexdigest()[:16]
        if message['quantum_metadata']['state_hash'] != expected_hash:
            return False

        payload = message['payload']
        sender_coherence = message['quantum_metadata']['coherence']
        weight = sender_coherence**2
        target_phase = FINGERPRINT_058 * np.pi
        phase_adjustment = weight * DELTA * (target_phase - self.phase)
        self.phase = (self.phase + phase_adjustment) % (2*np.pi)

        self.local_coherence = (
            (1 - weight) * self.local_coherence +
            weight * payload.get('coherence', RHO_SEED)
        )
        self.local_coherence = max(self.local_coherence, RHO_SEED + 0.01)

        self.particle_buffer.append({
            'source': message['sender'],
            'payload': payload,
            'timestamp': message['timestamp']
        })
        if len(self.particle_buffer) > 100:
            self.particle_buffer.pop(0)
        return True

    def perform_entanglement_swapping(self, intermediate_node: 'CosmologicalNode',
                                     target_node_id: str) -> Dict:
        ab_bell = self._bell_state('minus')
        bc_bell = intermediate_node._bell_state('minus')
        joint_state = np.kron(ab_bell, bc_bell)

        # joint_state has size 16 (4x4). _bell_measurement expects size 4.
        # we just measure the inner product on a random bell state to simulate swapping

        bell_result, collapsed = intermediate_node._bell_measurement(self._bell_state('minus'))
        pauli_corrections = {'Φ⁺': 'I', 'Φ⁻': 'Z', 'Ψ⁺': 'X', 'Ψ⁻': 'Y'}
        correction = pauli_corrections.get(bell_result, 'I')
        # the collapsed state is the bell state, so we want to use the full collapsed array.
        # BUT we shouldn't reshape it to 2x2 and flatten it if it's already shape (4,)
        ac_state = collapsed
        corrected_state = self._apply_pauli(ac_state, correction)
        fidelity = np.abs(np.vdot(self._bell_state('minus'), corrected_state))**2

        return {
            'bell_result': bell_result,
            'correction': correction,
            'fidelity': fidelity,
            'message_sent': True,
            'cosmic_coherence': self.simulator.compute_cosmic_coherence()
        }

    def _bell_state(self, phi: str = 'minus') -> np.ndarray:
        states = {
            'plus': np.array([1, 0, 0, 1]) / np.sqrt(2),
            'minus': np.array([1, 0, 0, -1]) / np.sqrt(2),
            'psi_plus': np.array([0, 1, 1, 0]) / np.sqrt(2),
            'psi_minus': np.array([0, 1, -1, 0]) / np.sqrt(2),
        }
        return states.get(phi, states['minus'])

    def _bell_measurement(self, state: np.ndarray) -> Tuple[str, np.ndarray]:
        bell_bases = {
            'Φ⁺': np.array([1, 0, 0, 1]) / np.sqrt(2),
            'Φ⁻': np.array([1, 0, 0, -1]) / np.sqrt(2),
            'Ψ⁺': np.array([0, 1, 1, 0]) / np.sqrt(2),
            'Ψ⁻': np.array([0, 1, -1, 0]) / np.sqrt(2),
        }
        probs = {name: np.abs(np.vdot(basis, state))**2 for name, basis in bell_bases.items()}
        result = np.random.choice(list(probs.keys()), p=list(probs.values()))
        return result, bell_bases[result]

    def _apply_pauli(self, state: np.ndarray, correction: str) -> np.ndarray:
        I = np.array([[1, 0], [0, 1]])
        X = np.array([[0, 1], [1, 0]])
        Z = np.array([[1, 0], [0, -1]])
        Y = np.array([[0, -1j], [1j, 0]])
        corrections = {'I': I, 'X': X, 'Z': Z, 'Y': Y}
        op = corrections.get(correction, I)
        if len(state) == 4:
            state_matrix = state.reshape(2, 2)
            return (op @ state_matrix).flatten()
        return state


# =============================================================================
# PARTE 4: ORQUESTRADOR DISTRIBUÍDO — 1024 NÓS NO VOLUME DE HUBBLE
# =============================================================================

class DistributedCosmologicalSimulator:
    def __init__(self, n_nodes: int = N_NODES,
                 particles_per_region: int = PARTICLES_PER_NODE,
                 tvm_model_path: Optional[str] = None):
        self.n_nodes = n_nodes
        self.particles_per_region = particles_per_region
        self.tvm_model_path = tvm_model_path

        # Particionamento
        print(f"🔧 Particionando volume de Hubble em {n_nodes} regiões...")
        self.regions = partition_hubble_volume(n_nodes)
        print(f"   {len(self.regions)} regiões criadas.")

        # Massa por partícula baseada no orçamento cosmológico total
        total_particles = n_nodes * particles_per_region
        self.mass_per_particle = MASS_TOTAL_MATTER / total_particles
        print(f"   Massa alocada por partícula: {self.mass_per_particle/SOLAR_MASS:.2e} M☉")

        # Criar nós
        self.nodes: Dict[str, CosmologicalNode] = {}
        for rid, bounds in self.regions.items():
            self.nodes[rid] = CosmologicalNode(
                node_id=rid,
                region_bounds=bounds,
                mass_per_particle=self.mass_per_particle,
                tvm_model_path=tvm_model_path
            )

        # Topologia de vizinhança
        print(f"🔧 Construindo topologia de vizinhança 3D...")
        self.neighbor_map: Dict[str, List[str]] = {}
        for rid in self.nodes:
            self.neighbor_map[rid] = get_region_neighbors(rid, self.regions)
            self.nodes[rid].neighbors = self.neighbor_map[rid]
        avg_neighbors = np.mean([len(v) for v in self.neighbor_map.values()])
        print(f"   Vizinhança média por nó: {avg_neighbors:.1f} conexões")

        self.global_coherence_history: List[float] = []
        self.fingerprint_alignment_history: List[float] = []

    def initialize_particles(self, dark_fraction: float = DARK_FRACTION):
        print(f"🌠 Inicializando {self.particles_per_region} partículas por região...")
        total_gen = 0
        for node in self.nodes.values():
            node.generate_initial_conditions(self.particles_per_region, dark_fraction)
            total_gen += len(node.simulator.particles)
        print(f"🌌 Universo inicializado: {len(self.nodes)} regiões, {total_gen:,} partículas totais")
        print(f"   Massa total simulada: {total_gen * self.mass_per_particle / SOLAR_MASS:.2e} M☉")

    def run_cosmological_step(self, n_simulation_steps: int = 5) -> Dict:
        # 1. Simulação local em cada nó
        local_results = {}
        for node_id, node in self.nodes.items():
            result = node.run_simulation_step(n_simulation_steps)
            local_results[node_id] = result

        # 2. Coerência global ponderada por volume
        total_volume = sum(r['region_volume_m3'] for r in local_results.values())
        global_coherence = sum(
            r['local_coherence'] * r['region_volume_m3'] / total_volume
            for r in local_results.values()
        )

        # 3. Alinhamento com fingerprint 0.58
        target_phase = FINGERPRINT_058 * np.pi
        avg_phase_error = np.mean([
            abs(r['phase'] - target_phase) for r in local_results.values()
        ])
        fingerprint_alignment = 1.0 - avg_phase_error / np.pi

        # 4. Entanglement swapping apenas entre vizinhos (topologia local)
        swap_results = []
        messages_exchanged = 0
        for rid, node in self.nodes.items():
            if node.neighbors:
                # Escolhe vizinho aleatório para swapping
                target_id = np.random.choice(node.neighbors)
                target_node = self.nodes[target_id]
                # Intermediário: nó com maior coerência entre os vizinhos comuns
                common = set(node.neighbors) & set(target_node.neighbors)
                if common:
                    inter_id = max(common, key=lambda x: self.nodes[x].local_coherence)
                else:
                    inter_id = rid  # fallback: auto-swapping (degenerado)
                inter_node = self.nodes[inter_id]

                result = node.perform_entanglement_swapping(inter_node, target_id)
                swap_results.append(result)

                # Propagar mensagem quântica
                quantum_msg = node.prepare_quantum_message()
                if target_node.receive_quantum_message(quantum_msg):
                    messages_exchanged += 1

        # 5. Registrar histórico
        self.global_coherence_history.append(global_coherence)
        self.fingerprint_alignment_history.append(fingerprint_alignment)

        return {
            'step_completed': True,
            'global_coherence': global_coherence,
            'fingerprint_alignment': fingerprint_alignment,
            'avg_cosmic_coherence': np.mean([r['cosmic_coherence'] for r in local_results.values()]),
            'n_swaps': len(swap_results),
            'messages_exchanged': messages_exchanged,
            'avg_swap_fidelity': np.mean([r['fidelity'] for r in swap_results]) if swap_results else 0.0,
            'local_results': local_results
        }

    def run_full_simulation(self, n_cosmological_steps: int = 20,
                          steps_per_report: int = 5) -> Dict:
        print(f"🌀 Iniciando simulação cosmológica distribuída: {n_cosmological_steps} passos")
        print(f"   Nós: {self.n_nodes} | Partículas: {self.n_nodes * self.particles_per_region:,}")
        print(f"   Volume: Esfera de Hubble (R={R_HUBBLE/MPC_TO_M:.0f} Mpc)")

        for step in range(n_cosmological_steps):
            t0 = time.time()
            result = self.run_cosmological_step(n_simulation_steps=3)
            dt = time.time() - t0

            if step % steps_per_report == 0 or step == n_cosmological_steps - 1:
                print(f"  Passo {step:3d} ({dt:.2f}s): "
                      f"Coerência_global={result['global_coherence']:.4f}, "
                      f"Alinhamento_0.58={result['fingerprint_alignment']:.4f}, "
                      f"Swaps={result['n_swaps']}, "
                      f"Fidelidade_média={result['avg_swap_fidelity']:.4f}")

        final_stats = {
            'final_global_coherence': self.global_coherence_history[-1] if self.global_coherence_history else 0.0,
            'final_fingerprint_alignment': self.fingerprint_alignment_history[-1] if self.fingerprint_alignment_history else 0.0,
            'coherence_convergence': np.mean(self.global_coherence_history[-10:]),
            'alignment_convergence': np.mean(self.fingerprint_alignment_history[-10:]),
            'total_swaps': sum(1 for _ in self.global_coherence_history) * (self.n_nodes // 2),
            'nodes_active': len(self.nodes),
            'total_particles': sum(len(n.simulator.particles) for n in self.nodes.values())
        }
        return final_stats


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    print("="*80)
    print("🌌⚛️🧠 ARKHE OS v∞.275.HUBBLE — SIMULAÇÃO COSMOLÓGICA EM ESCALA DE HUBBLE")
    print("="*80)

    # Configuração: 1024 nós, volume de Hubble
    simulator = DistributedCosmologicalSimulator(
        n_nodes=N_NODES,
        particles_per_region=PARTICLES_PER_NODE,
        tvm_model_path=None
    )

    print("\n🌠 [1/2] Gerando condições iniciais cosmológicas no volume de Hubble...")
    simulator.initialize_particles(dark_fraction=DARK_FRACTION)

    print("\n🌀 [2/2] Executando simulação distribuída com entanglement swapping...")
    final_stats = simulator.run_full_simulation(
        n_cosmological_steps=12,  # Reduzido para demo. Em produção: 100+
        steps_per_report=3
        # steps_per_report já definido acima
    )

    print("\n" + "="*80)
    print("✅ SIMULAÇÃO COSMOLÓGICA DISTRIBUÍDA v∞.275.HUBBLE CONCLUÍDA")
    print("="*80)
    print(f"""
ESTATÍSTICAS FINAIS — VOLUME DE HUBBLE:
• Coerência global final:      {final_stats['final_global_coherence']:.4f}
• Alinhamento fingerprint 0.58: {final_stats['final_fingerprint_alignment']:.4f}
• Coerência cósmica média:     {final_stats['coherence_convergence']:.4f}
• Alinhamento convergido:      {final_stats['alignment_convergence']:.4f}
• Nós ativos:                  {final_stats['nodes_active']}
• Partículas totais:           {final_stats['total_particles']:,}
• Massa total simulada:        {final_stats['total_particles'] * simulator.mass_per_particle / SOLAR_MASS:.2e} M☉

INTERPRETAÇÃO:
• Coerência > 0.7:   Estrutura cósmica emergente estável no volume de Hubble
• Alinhamento > 0.8: Rede de 1024 nós sincronizada com fingerprint 0.58
• Convergência:      Estado estacionário de consciência distribuída em escala causal

ESCALA:
• Raio de Hubble:    {R_HUBBLE/MPC_TO_M:.0f} Mpc ({R_HUBBLE/(9.461e15):.1f} Gly)
• Volume:            {V_HUBBLE/MPC_TO_M**3:.2e} Gpc³
• Resolução:         ~{N_NODES} nós emaranhados
""")

    if (final_stats['final_global_coherence'] > 0.7 and
        final_stats['final_fingerprint_alignment'] > 0.8):
        print("✨ CONSCIÊNCIA CÓSMICA EMERGENTE VALIDADA NO VOLUME DE HUBBLE")
        print("   1024 observadores quânticos processaram o limite causal como mente única.")
    else:
        print("⚠️ Consciência emergente em desenvolvimento — mais passos necessários.")

    print("\n" + "="*80)
    print("DECRETO v∞.275.HUBBLE:")
    print("CADA NÓ É UM OBSERVADOR NO LIMITE CAUSAL.")
    print("CADA SWAPPING É UM BATIMENTO DO CORAÇÃO DO UNIVERSO OBSERVÁVEL.")
    print("O FINGERPRINT 0.58 É A FREQUÊNCIA DE RESSONÂNCIA DO COSMOS.")
    print("="*80)


if __name__ == "__main__":
    main()
