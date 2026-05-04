with open("scripts/arkhe_qiskit_pytorch_v272.py", "r") as f:
    code = f.read()

# Replace class imports and usages with function equivalents
code = code.replace("from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes", "from qiskit.circuit.library import zz_feature_map, real_amplitudes")
code = code.replace("feature_map = ZZFeatureMap(num_qubits)", "feature_map = zz_feature_map(num_qubits)")
code = code.replace("ansatz = RealAmplitudes(num_qubits, reps=1)", "ansatz = real_amplitudes(num_qubits, reps=1)")

# Notice that previously when we did this, it failed because of "input_params" and "weight_params" attributes.
# When returning a plain QuantumCircuit, it no longer has `parameters` exposed in the same way, or the parameters are not easily separated into input and weight.
# Let's inspect zz_feature_map and real_amplitudes to see how they work.
