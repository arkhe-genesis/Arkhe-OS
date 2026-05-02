#!/usr/bin/env python3
"""
living_interpretability_framework.py
Framework para publicar a arquitetura auto-organizativa como sistema de interpretabilidade vivo.
"""
import numpy as np
import json
from datetime import datetime
from pathlib import Path

class LivingInterpretabilityPublisher:
    """Publica evidências contínuas da geometria interna do Crystal Brain."""

    def __init__(self, output_dir='publish/interpretability',
                 update_interval_epochs=5):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.update_interval = update_interval_epochs
        self.publication_log = []

    def generate_geometric_evidence(self, epoch_data, ising_result,
                                    optimization_history, zee200_proofs=None):
        """
        Gera pacote de evidência geométrica para publicação.
        """
        evidence = {
            'timestamp': datetime.now().isoformat(),
            'epoch': epoch_data['epoch'],
            'parameters': {
                'kappa': epoch_data['kappa'],
                'lambda_l1': epoch_data['lambda_l1'],
                'binarization_threshold': epoch_data['binarization_threshold'],
                'embedding_dim': epoch_data['embedding_dim']
            },
            'geometric_state': {
                'capture_fraction': ising_result['capture_fraction'],
                'n_communities': len(ising_result['community_details']),
                'regime_distribution': {
                    regime: sum(1 for info in ising_result['community_details'].values()
                               if info['regime'] == regime)
                    for regime in ['CAPTURE', 'SHATTERING', 'DILUTION', 'AMBIGUOUS']
                },
                'dominant_manifolds': [
                    {
                        'community_id': cid,
                        'regime': info['regime'],
                        'cohesion_rho': info['rho'],
                        'size': len(info['crystals']),
                        'manifold_dim': info.get('manifold_dim', None)
                    }
                    for cid, info in ising_result['community_details'].items()
                    if info['regime'] == 'CAPTURE'
                ]
            },
            'optimization_trajectory': {
                'score_evolution': [h.get('score', h.get('capture_fraction')) for h in optimization_history[-20:]],
                'parameter_stability': {
                    name: np.std([h.get('params', h)[name] for h in optimization_history[-10:]]) if len(optimization_history) > 1 else 0
                    for name in ['kappa', 'lambda_l1', 'binarization_threshold', 'embedding_dim']
                }
            },
            'verifiable_proofs': [
                {
                    'proof_hash': proof['proof_hash'],
                    'community_id': proof.get('community_id', 'steering_proof'),
                    'block_id': proof.get('timestamp', 'N/A'),
                    'manifold_dim': proof.get('manifold_dim', 3),
                    'epsilon': proof.get('epsilon', 0.01)
                }
                for proof in (zee200_proofs or [])
            ] if zee200_proofs else None
        }

        return evidence

    def publish_evidence(self, evidence, include_raw_data=False):
        """
        Publica evidência no diretório de saída.
        """
        # Nome do arquivo baseado em timestamp e epoch
        filename = f"evidence_epoch_{evidence['epoch']}_{evidence['timestamp'][:10]}.json"
        filepath = self.output_dir / filename

        # Preparar dados para publicação
        publish_data = evidence.copy()
        if not include_raw_data:
            # Remover campos grandes se necessário
            publish_data.pop('optimization_trajectory', None)

        # Salvar
        with open(filepath, 'w') as f:
            json.dump(publish_data, f, indent=2)

        # Atualizar índice mestre
        index_path = self.output_dir / 'index.json'
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)
        else:
            index = {'publications': [], 'last_updated': None}

        index['publications'].append({
            'filename': filename,
            'epoch': evidence['epoch'],
            'timestamp': evidence['timestamp'],
            'capture_fraction': evidence['geometric_state']['capture_fraction'],
            'proofs_count': len(evidence.get('verifiable_proofs') or [])
        })
        index['last_updated'] = datetime.now().isoformat()

        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

        self.publication_log.append(filepath)
        print(f"📤 Evidência publicada: {filepath.name}")
        return filepath

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish-first-evidence', action='store_true')
    args = parser.parse_args()

    if args.publish_first_evidence:
        publisher = LivingInterpretabilityPublisher()
        # Mock evidence for testing
        mock_evidence = publisher.generate_geometric_evidence(
            epoch_data={'epoch': 1, 'kappa': 0.75, 'lambda_l1': 0.003, 'binarization_threshold': 0.1, 'embedding_dim': 3},
            ising_result={'capture_fraction': 0.85, 'community_details': {0: {'regime': 'CAPTURE', 'rho': 0.9, 'crystals': [1,2,3], 'manifold_dim': 3}}},
            optimization_history=[{'kappa': 0.75, 'lambda_l1': 0.003, 'binarization_threshold': 0.1, 'embedding_dim': 3, 'capture_fraction': 0.85}]
        )
        publisher.publish_evidence(mock_evidence)
