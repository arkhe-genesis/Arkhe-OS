with open("scripts/arkhe_qiskit_pytorch_v272.py", "r") as f:
    code = f.read()

code = code.replace("from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes", "from qiskit.circuit.library import zz_feature_map, real_amplitudes")
code = code.replace("feature_map = ZZFeatureMap(num_qubits)", "feature_map = zz_feature_map(num_qubits)")
code = code.replace("ansatz = RealAmplitudes(num_qubits, reps=1)", "ansatz = real_amplitudes(num_qubits, reps=1)")

with open("scripts/arkhe_qiskit_pytorch_v272.py", "w") as f:
    f.write(code)
