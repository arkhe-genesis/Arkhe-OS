import json
import tempfile
import os

class SubstratoLearnMechanisticInterpretability:
    def canonize(self):
        report = {
            "Title": "Learn Mechanistic Interpretability - A hands-on curriculum",
            "Description": "A 6-step open-source learning path from \"I've never trained a neural network\" to \"I can read current mech interp papers\". Each step is a self-contained project that replicates a famous experiment, teaches one new big idea, and assumes only what previous steps already covered.",
            "Features": [
                "00-mnist-templates: Olah-era weight visualisation. Teaches that weights are interpretable.",
                "01-toy-models-superposition: Replicates Elhage et al. 2022. Teaches that features ≠ neurons (superposition).",
                "02-grokking-modular-addition: Replicates Nanda et al. 2023. Teaches that models learn algorithms, not just templates.",
                "03-induction-heads: Replicates Olsson et al. 2022. Teaches that real transformers do work via attention-head circuits.",
                "04-ioi-circuit: Replicates Wang et al. 2022. Teaches activation patching - verifying circuits causally.",
                "05-sparse-autoencoders: Replicates Cunningham et al. 2023. Teaches dictionary learning - automatically finding features."
            ],
            "Architecture": [
                "Each step contains a teaching README.md and a runnable Jupyter notebook.",
                "Designed to drop straight into Google Colab.",
                "Self-contained projects that assume only what previous steps already covered."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_catmcgee_learn_mechanistic_interpretability_")
        with os.fdopen(fd, 'w', encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)

        print("Canonized Learn Mechanistic Interpretability. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoLearnMechanisticInterpretability()
    substrate.canonize()
