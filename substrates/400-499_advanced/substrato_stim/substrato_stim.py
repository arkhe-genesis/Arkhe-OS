import json
import tempfile
import os

class SubstratoStim:
    def canonize(self):
        report = {
            "Title": "Stim",
            "Description": "A fast stabilizer circuit library.",
            "Features": [
                "Really fast simulation of stabilizer circuits.",
                "Semi-automatic decoder configuration. stim.Circuit.detector_error_model() converts a noisy circuit into a detector error model (a Tanner graph) which can be used to configure decoders.",
                "Useful building blocks for working with stabilizers, such as stim.PauliString, stim.Tableau, and stim.TableauSimulator."
            ],
            "Limitations": [
                "There is no support for non-Clifford operations, such as T gates and Toffoli gates. Only stabilizer operations are supported.",
                "stim.Circuit only supports Pauli noise channels (eg. no amplitude decay).",
                "stim.Circuit only supports single-control Pauli feedback."
            ],
            "DesignPhilosophy": [
                "Performance is king. The goal is not to be fast enough, it is to be fast in an absolute sense.",
                "Bottom up. Stim is intended to be like an assembly language: a mostly straightforward layer upon which more complex layers can be built.",
                "Backwards compatibility. Stim's Python package uses semantic versioning."
            ],
            "CoreImprovements": [
                "Vectorized code. Stim's hot loops are heavily vectorized, using 256 bit wide AVX instructions.",
                "Reference Frame Sampling. When bulk sampling, Stim only uses a general stabilizer simulator for an initial reference sample. After that, it cheaply derives as many samples as needed by propagating simulated errors diffed against the reference.",
                "Inverted Stabilizer Tableau. When doing general stabilizer simulation, Stim tracks the inverse of the stabilizer tableau that was historically used. This has the unexpected benefit of making measurements that commute with the current stabilizers take linear time instead of quadratic time."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_stim_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Stim. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoStim()
    substrate.canonize()
