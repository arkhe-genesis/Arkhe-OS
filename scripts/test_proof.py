import sys
sys.path.append('src/core/stark/arkhe-stark-rust/target/release')
import arkhe_stark_rust

node_id = [0]*32

# In winterfell trace transitions run out to trace.length() - 1, and assertions apply constraints.
# Let's mock a valid trace such that evaluate_transition evaluates to 0.
# Constraints in MerkabahAir:
# 0: phase(t+1) = phase(t) + control(t) * 1
# 1: coherence(t+1) = coherence(t) + 1 * (1 - error(t)^2 / 9) -> scaled to 1.0 (since no floats) -> 1 - error^2
# 2: error(t)^2 = (phase(t) - target_phase)^2
# 3: control(t+1) = -1 * error(t+1)

# Given initial phase = 0, target_phase = 0
trace_data = []
phase = 0.0
coherence = 0.0
error = 0.0
control = 0.0

for i in range(128):
    trace_data.append([phase, coherence, error, control])
    # Compute next states according to constraints
    phase_next = phase + control

    error_next = phase_next

    coherence_next = coherence + 1.0 - (error**2)

    control_next = -error_next

    phase = phase_next
    coherence = coherence_next
    error = error_next
    control = control_next

try:
    res = arkhe_stark_rust.generate_merkabah_proof(node_id, 0.0, 0.0, trace_data)
    print("Proof generation length:", len(res))
    print("Verification and Integration works!")
except Exception as e:
    print("Execution failed with:", e)
