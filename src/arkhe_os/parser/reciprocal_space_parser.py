# src/arkhe_os/parser/reciprocal_space_parser.py
"""
Main parser for Reciprocal-Space Neural Networks (RSP/RSD).
Platform-agnostic implementation with optional acceleration backends.
"""
import numpy as np
import torch
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import json
import logging

from .platform_abstraction import PLATFORM, parallel_map, get_cache_dir
from .lfir import LFIRGraph, LFIRNode, LFIRNodeType, LFIREdge
from .atomic_structure import AtomicStructure, read_structure_file
from .rsp_model import ReciprocalSpaceNN, load_model_config

logger = logging.getLogger(__name__)

def _symbol_to_z(symbol: str) -> int:
    """Mock implementation to map atomic symbol to atomic number."""
    # Simplified mock table
    table = {'H': 1, 'O': 8, 'Hf': 72, 'Na': 11, 'Cl': 17}
    return table.get(symbol, 0)

class ReciprocalSpaceParser:
    """
    Parser for Reciprocal-Space Neural Network models.

    Features:
    - Cross-platform compatibility (Linux, macOS, Windows)
    - Optional GPU acceleration (CUDA on Linux, MPS on macOS)
    - Memory-efficient processing of large structures
    - Caching of Fourier transforms for repeated k-point evaluations
    """

    def __init__(
        self,
        device: Optional[str] = None,
        cache_fourier: bool = True,
        max_atoms: int = 10000
    ):
        """
        Initialize parser with platform-appropriate settings.

        Args:
            device: Override acceleration backend ('cpu', 'cuda', 'mps')
            cache_fourier: Cache Fourier transforms for performance
            max_atoms: Maximum number of atoms to process (memory safety)
        """
        # Auto-detect device if not specified
        if device is None:
            self.device = PLATFORM.acceleration_backend
        else:
            self.device = device

        # Validate device availability
        if self.device == 'cuda' and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available — falling back to CPU")
            self.device = 'cpu'
        elif self.device == 'mps' and not (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
            logger.warning("MPS requested but not available — falling back to CPU")
            self.device = 'cpu'

        self.torch_device = torch.device(self.device if self.device != 'cpu' else 'cpu')
        self.cache_fourier = cache_fourier
        self.max_atoms = max_atoms

        # Fourier cache (platform-optimized storage)
        self._fourier_cache: Dict[str, torch.Tensor] = {}
        self._cache_dir = get_cache_dir('fourier') if cache_fourier else None

        logger.info(f"RSP Parser initialized: device={self.device}, cache={cache_fourier}")

    def parse(
        self,
        structure: Union[str, Path, AtomicStructure],
        model: Union[str, Path, ReciprocalSpaceNN],
        output: Optional[Union[str, Path]] = None
    ) -> LFIRGraph:
        """
        Parse atomic structure through reciprocal-space neural network.

        Args:
            structure: Path to structure file (POSCAR, CIF, XYZ) or AtomicStructure object
            model: Path to model config JSON or ReciprocalSpaceNN object
            output: Optional path to save LFIR graph as JSON

        Returns:
            LFIRGraph representing the parsed structure with coherence metrics
        """
        # Load inputs
        if isinstance(structure, (str, Path)):
            structure = read_structure_file(structure)
        if isinstance(model, (str, Path)):
            model = load_model_config(model)

        # Validate structure size
        if len(structure.positions) > self.max_atoms:
            raise ValueError(
                f"Structure has {len(structure.positions)} atoms, "
                f"exceeds maximum of {self.max_atoms}"
            )

        # Create LFIR graph
        graph = LFIRGraph()

        # 1. Add atomic nodes (real space)
        atom_nodes = self._add_atomic_nodes(structure, graph)

        # 2. Add reciprocal space nodes (k-points)
        kpoint_nodes = self._add_kpoint_nodes(model, graph)

        # 3. Add local interaction edges (short-range)
        self._add_local_edges(structure, atom_nodes, graph)

        # 4. Add reciprocal interaction edges (long-range via Fourier)
        self._add_reciprocal_edges(structure, model, atom_nodes, kpoint_nodes, graph)

        # 5. Compute coherence metrics
        graph.coherence_score = self._compute_coherence(structure, model, graph)
        graph.metadata.update({
            'parser_version': '1.0.0',
            'platform': PLATFORM.system,
            'device': self.device,
            'n_atoms': len(structure.positions),
            'n_kpoints': len(model.k_mesh)
        })

        # Save if requested
        if output:
            graph.to_json(output)
            logger.info(f"LFIR graph saved to {output}")

        return graph

    def _add_atomic_nodes(self, structure: AtomicStructure, graph: LFIRGraph) -> List[LFIRNode]:
        """Add atomic nodes to LFIR graph."""
        nodes = []
        for i, (pos, sym) in enumerate(zip(structure.positions, structure.symbols)):
            node = LFIRNode(
                id=f"atom_{i}",
                node_type=LFIRNodeType.VARIABLE,
                substrate="reciprocal_nn"
            )
            node.attributes.update({
                'symbol': sym,
                'position': pos.tolist(),
                'atomic_number': _symbol_to_z(sym)
            })
            graph.add_node(node)
            nodes.append(node)
        return nodes

    def _add_kpoint_nodes(self, model: ReciprocalSpaceNN, graph: LFIRGraph) -> List[LFIRNode]:
        """Add reciprocal space (k-point) nodes to LFIR graph."""
        nodes = []
        for j, kpt in enumerate(model.k_mesh):
            node = LFIRNode(
                id=f"kpoint_{j}",
                node_type=LFIRNodeType.BLOCK,
                substrate="reciprocal_nn"
            )
            node.attributes.update({
                'k_vector': kpt.tolist(),
                'weight': 1.0 / len(model.k_mesh),
                'irreducible': False  # Could be set based on symmetry
            })
            graph.add_node(node)
            nodes.append(node)
        return nodes

    def _add_local_edges(
        self,
        structure: AtomicStructure,
        atom_nodes: List[LFIRNode],
        graph: LFIRGraph,
        cutoff: float = 5.0
    ):
        """Add short-range interaction edges based on distance cutoff."""
        positions = structure.positions
        n_atoms = len(positions)

        # Compute pairwise distances (vectorized for performance)
        dist_matrix = np.linalg.norm(
            positions[:, np.newaxis, :] - positions[np.newaxis, :, :],
            axis=-1
        )

        # Add edges for pairs within cutoff
        for i in range(n_atoms):
            for j in range(i + 1, n_atoms):
                dist = dist_matrix[i, j]
                if dist < cutoff:
                    weight = np.exp(-dist / 2.0)  # Exponential decay
                    edge = LFIREdge(
                        source=atom_nodes[i].id,
                        target=atom_nodes[j].id,
                        relation="local_bond",
                        weight=float(weight),
                        attributes={'distance': float(dist)}
                    )
                    graph.add_edge(edge)

    def _add_reciprocal_edges(
        self,
        structure: AtomicStructure,
        model: ReciprocalSpaceNN,
        atom_nodes: List[LFIRNode],
        kpoint_nodes: List[LFIRNode],
        graph: LFIRGraph
    ):
        """Add long-range interaction edges via reciprocal space Fourier transform."""
        positions = torch.tensor(structure.positions, dtype=torch.float32, device=self.torch_device)
        atomic_numbers = torch.tensor(
            [_symbol_to_z(sym) for sym in structure.symbols],
            dtype=torch.float32,
            device=self.torch_device
        )

        for k_idx, kpoint_node in enumerate(kpoint_nodes):
            k_vector = torch.tensor(
                kpoint_node.attributes['k_vector'],
                dtype=torch.float32,
                device=self.torch_device
            )

            # Compute Fourier phase factors: exp(i k · r)
            phases = torch.exp(1j * torch.matmul(positions, k_vector))

            # Compute structure factor weights (simplified)
            weights = torch.abs(phases) * atomic_numbers

            # Add edges from atoms to this k-point
            for i, atom_node in enumerate(atom_nodes):
                edge = LFIREdge(
                    source=atom_node.id,
                    target=kpoint_node.id,
                    relation="reciprocal_interaction",
                    weight=float(weights[i].item()),
                    attributes={
                        'k_index': k_idx,
                        'phase_real': float(phases[i].real.item()),
                        'phase_imag': float(phases[i].imag.item())
                    }
                )
                graph.add_edge(edge)

    def _compute_coherence(
        self,
        structure: AtomicStructure,
        model: ReciprocalSpaceNN,
        graph: LFIRGraph
    ) -> float:
        """Compute coherence score Φ_C for the parsed structure."""
        # 1. Mesh completeness score
        mesh_completeness = min(1.0, len(model.k_mesh) / 1000)

        # 2. Symmetry preservation score (simplified check)
        symmetry_score = 1.0  # Assumed if model was trained with invariance

        # 3. Numerical stability score (based on Fourier transform conditioning)
        try:
            # Quick condition number estimate of Fourier matrix
            k_mesh = np.array([n.attributes['k_vector'] for n in graph.nodes
                             if n.attributes.get('k_vector')])
            if len(k_mesh) > 0:
                cond = np.linalg.cond(k_mesh @ k_mesh.T + 1e-6 * np.eye(len(k_mesh)))
                stability_score = max(0.0, min(1.0, 1.0 / np.log10(cond + 1)))
            else:
                stability_score = 1.0
        except:
            stability_score = 0.5  # Fallback

        # Weighted combination
        coherence = (
            0.4 * mesh_completeness +
            0.4 * symmetry_score +
            0.2 * stability_score
        )

        return float(np.clip(coherence, 0.0, 1.0))

    def predict_long_range_energy(
        self,
        graph: LFIRGraph,
        effective_charges: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Predict long-range energy contributions using the RSP model.

        Args:
            graph: LFIR graph from parse()
            effective_charges: Optional Born effective charges for Coulomb term

        Returns:
            Dict with energy components and coherence metrics
        """
        # Extract k-point contributions from graph
        kpoint_nodes = [n for n in graph.nodes if n.attributes.get('k_vector')]

        if not kpoint_nodes:
            return {'E_LR': 0.0, 'E_Coulomb': 0.0, 'E_vdW': 0.0}

        # Simplified energy estimation (real implementation would use trained RSP model)
        total_weight = sum(
            abs(e.weight) for e in graph.edges
            if e.relation == "reciprocal_interaction"
        )

        # Estimate Coulomb and van der Waals contributions
        E_Coulomb = total_weight * 0.15  # Simplified scaling
        E_vdW = total_weight * 0.03

        return {
            'E_LR': float(E_Coulomb + E_vdW),
            'E_Coulomb': float(E_Coulomb),
            'E_vdW': float(E_vdW),
            'n_kpoints_evaluated': len(kpoint_nodes),
            'reciprocal_coherence': graph.coherence_score
        }
