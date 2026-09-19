"""Q4_K_M quantization metadata."""
def quantize_q4_k_m(experts):
    for expert in experts: expert.update(quantization="Q4_K_M", bits_per_weight=4.0)
    return experts
