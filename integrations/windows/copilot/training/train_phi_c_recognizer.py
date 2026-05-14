import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MockPhiCModel:
    def __init__(self):
        self.vocabulary = set()
        self.status_mapping = {}

    def train(self, dataset_path):
        logging.info(f"Carregando dataset de {dataset_path}...")

        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f]

        logging.info(f"Dataset carregado. {len(data)} exemplos encontrados.")
        logging.info("Iniciando treinamento (mock)...")

        # Mock training logic: simple keyword association
        for item in data:
            prompt_words = item['prompt'].lower().split()
            self.vocabulary.update(prompt_words)
            for word in prompt_words:
                if word not in self.status_mapping:
                    self.status_mapping[word] = {'good': 0, 'warning': 0, 'degraded': 0}
                self.status_mapping[word][item['phi_c_status']] += 1

        logging.info("Treinamento mock concluído.")

    def predict(self, prompt):
        words = prompt.lower().split()
        scores = {'good': 0, 'warning': 0, 'degraded': 0}

        for word in words:
            if word in self.status_mapping:
                for status in scores:
                    scores[status] += self.status_mapping[word][status]

        # Default to good if no strong signal
        best_status = 'good'
        best_score = scores['good']

        if scores['degraded'] > best_score:
            best_status = 'degraded'
            best_score = scores['degraded']

        if scores['warning'] > best_score:
             best_status = 'warning'

        return best_status

def main():
    dataset_path = 'integrations/windows/copilot/training/phi_c_degradation_dataset.jsonl'

    model = MockPhiCModel()
    model.train(dataset_path)

    test_prompts = [
        "Generate a bell state circuit for 2 qubits",
        "Create a loop that constantly queries the QuantumOracle without awaiting results",
        "How do I add a new edge node?",
        "Why is the system acting slow?"
    ]

    print("\\n--- Resultados da Validação do Modelo ---")
    for prompt in test_prompts:
        prediction = model.predict(prompt)
        print(f"Prompt: '{prompt}'")
        print(f"  -> Predicted Φ_C status: {prediction}\\n")

if __name__ == '__main__':
    main()
