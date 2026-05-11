// Benchmark browser vs Node vs serverless
// Benchmark suite to evaluate the WASM implementation across different environments

// Note: To be run with criterion or wasm-bindgen-test

pub fn benchmark_keccak() {
    let data = b"ARKHE_BENCHMARK_PAYLOAD";
    for _ in 0..1000 {
        let _hash = arkhe_wasm::crypto::keccak::keccak256(data);
    }
}

pub fn benchmark_causal_proof() {
    let prover = arkhe_wasm::crypto::zk::causal::CausalConsistencyProver::new();
    let path = vec![
        alloc::string::String::from("A"),
        alloc::string::String::from("B"),
        alloc::string::String::from("C"),
    ];
    let edge_weights = vec![0.5, 0.4];
    let consistencies = vec![0.9, 0.95];
    let temporal_deltas = vec![0.0, 0.0];

    for _ in 0..100 {
        let _proof = prover.prove(&path, &edge_weights, &consistencies, &temporal_deltas, 1.0, 0.8);
    }
}
