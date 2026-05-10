import json
import numpy as np
import time
from pathlib import Path


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class LivingInterpretabilityPublisher:
    def __init__(self, output_dir='publish/interpretability', update_interval_epochs=5):
        self.output_dir = Path(output_dir)
        self.update_interval_epochs = update_interval_epochs
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # init index
        self.index_path = self.output_dir / 'index.json'
        if not self.index_path.exists():
            with open(self.index_path, 'w') as f:
                json.dump({'publications': []}, f, cls=NumpyEncoder)

    def generate_geometric_evidence(self, epoch_data, ising_result, optimization_history, zee200_proofs):
        evidence = {
            'timestamp': time.time(),
            'epoch': epoch_data.get('epoch', 0),
            'parameters': epoch_data.get('params', {}),
            'geometric_state': {
                'capture_fraction': ising_result.get('capture_fraction', 0.0),
                'dominant_manifolds': [
                    {'community_id': cid, **details}
                    for cid, details in ising_result.get('community_details', {}).items()
                    if details.get('regime') == 'CAPTURE'
                ]
            },
            'optimization_trajectory': optimization_history,
            'proofs': zee200_proofs
        }

        # update epoch parameter values into evidence structure
        for param in ['kappa', 'lambda_l1', 'binarization_threshold', 'embedding_dim']:
             if param in epoch_data:
                  evidence['parameters'][param] = epoch_data[param]

        return evidence

    def publish_evidence(self, evidence, include_raw_data=False):
        epoch = evidence['epoch']
        filename = f'evidence_epoch_{epoch}.json'
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(evidence, f, indent=2, cls=NumpyEncoder)

        # Update index
        with open(self.index_path, 'r') as f:
            index = json.load(f)

        index['publications'].append({
            'epoch': epoch,
            'capture_fraction': evidence['geometric_state']['capture_fraction'],
            'filepath': str(filepath)
        })

        with open(self.index_path, 'w') as f:
            json.dump(index, f, indent=2, cls=NumpyEncoder)

        return filepath
