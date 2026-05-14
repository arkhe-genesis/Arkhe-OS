import os
class PublicEpigenomeLoader:
    def search_datasets(self, *args, **kwargs):
        return ["fake_dataset_1"]

    def load_as_epigenetic_states(self, dataset, region=None):
        return []

    def load_chip_atac_data(self, dataset_id):
        import numpy as np
        return np.random.rand(100)

    def validate_experimental_predictions(self, predicted_states, chip_atac_data):
        import numpy as np
        if len(predicted_states) == 0:
            return 0.0
        # Mock calculation: mean squared error or fidelity
        fidelity = np.mean(chip_atac_data[:len(predicted_states)])
        mse = np.var(chip_atac_data[:len(predicted_states)])
        return {"fidelity": fidelity, "mse": mse}
