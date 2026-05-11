# arkhe_1q/cluster/coherence_cluster.py
import torch
from typing import Dict, List

class CoherenceCluster:
    """
    Cluster de 128 células FRC-2G com transporte paralelo de 2-formas.
    """

    def __init__(self, cluster_id: str, cells: List['FRC2GCell'], config: 'ClusterConfig'):
        self.cluster_id = cluster_id
        self.cells = {cell.cell_id: cell for cell in cells}
        self.config = config

        # Grafo de conectividade intra-cluster (small-world)
        self.connectivity_graph = self._build_smallworld_graph(
            n_nodes=len(cells),
            avg_degree=config.avg_intra_degree,
            rewiring_prob=0.15
        )

        # Operador de transporte paralelo de 2-formas
        self.transport_2form = ParallelTransport2Form(
            manifold_dim=5,
            connection_order=2,  # correção de curvatura de 2ª ordem
            numerical_tolerance=1e-8
        )

        # Agregador de Φ_C multi-escala
        self.phi_c_aggregator = MultiScaleCoherenceAggregator(
            num_scales=config.num_scales,
            aggregation_kernel='gaussian_weighted'
        )

    def synchronize_cells(self, source_cell_id: str, target_cell_ids: List[str],
                         form_degree: int = 2) -> Dict:
        """Sincroniza estado de célula fonte para múltiplos alvos via TPH."""
        source_cell = self.cells[source_cell_id]
        results = {}

        for target_id in target_cell_ids:
            target_cell = self.cells[target_id]

            # Extrair forma de borda da célula fonte
            edge_form = source_cell.extract_boundary_form(
                degree=form_degree,
                direction='outgoing'
            )

            # Aplicar transporte paralelo hierárquico
            transported_form = self.transport_2form.transport(
                form=edge_form,
                source_metric=source_cell.manifold_5d.get_metric(),
                target_metric=target_cell.manifold_5d.get_metric(),
                geodesic_path=self.connectivity_graph.shortest_path(
                    source_cell_id, target_id
                )
            )

            # Injetar forma transportada na célula alvo
            target_cell.inject_boundary_form(
                form=transported_form,
                direction='incoming'
            )

            results[target_id] = {
                'transport_cost': self.transport_2form.estimate_cost(
                    edge_form, source_cell_id, target_id
                ),
                'coherence_preservation': self.transport_2form.estimate_coherence_loss(
                    edge_form, form_degree
                )
            }

        return results

    def compute_cluster_phi_c(self) -> Dict[str, torch.Tensor]:
        """Computa espectro de coerência agregado do cluster."""
        # Coletar Φ_C espectral de cada célula
        cell_spectra = {
            cid: cell.phi_c_monitor.get_current_spectrum()
            for cid, cell in self.cells.items()
        }

        # Agregar via kernel multi-escala
        aggregated_spectrum = self.phi_c_aggregator.aggregate(
            cell_spectra,
            weights={cid: cell.phi_c_monitor.get_confidence()
                    for cid, cell in self.cells.items()}
        )

        return {
            'cluster_id': self.cluster_id,
            'aggregated_phi_c_spectrum': aggregated_spectrum,
            'cell_contributions': {
                cid: spec.mean().item()
                for cid, spec in cell_spectra.items()
            },
            'coherence_uniformity': self.phi_c_aggregator.compute_uniformity(
                list(cell_spectra.values())
            )
        }
