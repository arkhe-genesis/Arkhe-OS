use arkhe_neural_cartography::{Proofreader, NeuralCartographer};
use arkhe_neural_cartography::mapper::{ContinentalMind, ContinentalMindLayer};
use arkhe_neural_cartography::proofreader::ActivationRecord;

#[test]
fn test_extraction_and_proofreading() {
    // Mock the ContinentalMind model with simple layers and weights
    let model = ContinentalMind {
        layers: vec![
            ContinentalMindLayer {
                weight: vec![
                    vec![0.5, -0.1], // weak connection
                    vec![1.2, 0.0]
                ]
            },
            ContinentalMindLayer {
                weight: vec![
                    vec![0.8, 0.2]
                ]
            }
        ]
    };

    let proofreader = Proofreader {
        similarity_threshold: 0.95,
        min_activation_variance: 0.1,
        min_weight: 0.15,
    };

    let activations = ActivationRecord {};

    let mut cartographer = NeuralCartographer::new(proofreader);
    let connectome = cartographer.process_model(&model, &activations);

    // Initial synapses before pruning:
    // L0: 0.5, -0.1, 1.2
    // L1: 0.8, 0.2
    // After pruning with min_weight=0.15:
    // Expected remaining weights: 0.5, 1.2, 0.8, 0.2
    // So length should be 4.

    assert_eq!(connectome.synapses.len(), 4);

    let weights: std::collections::HashSet<String> = connectome
        .synapses
        .iter()
        .map(|s| format!("{:.1}", s.weight))
        .collect();

    assert!(weights.contains("0.5"));
    assert!(weights.contains("1.2"));
    assert!(weights.contains("0.8"));
    assert!(weights.contains("0.2"));
}
