"""Dense-to-MoE upcycling."""
def upcycle_dense_to_moe(dense_model, num_experts: int = 1000):
    if num_experts <= 0: raise ValueError("num_experts must be positive")
    return [{"id": i, "weights": dense_model.ffn_weights.copy(), "country": "BR"} for i in range(num_experts)]
