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

#[test]
fn test_cell_classification() {
    let mut connectome = arkhe_neural_cartography::connectome::Connectome::new();
    connectome.add_synapse(arkhe_neural_cartography::connectome::Synapse {
        pre_neuron: arkhe_neural_cartography::connectome::NeuronId(0, 0), // Sum: 0 (ET)
        post_neuron: arkhe_neural_cartography::connectome::NeuronId(0, 1), // Sum: 1 (IT)
        weight: 1.0,
        activation_correlation: 0.0,
        is_excitatory: true,
        layer: 0,
        head: None,
    });

    let classifications = arkhe_neural_cartography::cell_types::classify_cell_types(&connectome);

    assert!(matches!(classifications.get(&arkhe_neural_cartography::connectome::NeuronId(0, 0)), Some(arkhe_neural_cartography::cell_types::CellType::ET)));
    assert!(matches!(classifications.get(&arkhe_neural_cartography::connectome::NeuronId(0, 1)), Some(arkhe_neural_cartography::cell_types::CellType::IT)));
}

#[test]
fn test_wiring_rules() {
    let connectome = arkhe_neural_cartography::connectome::Connectome::new();
    let cell_types = std::collections::HashMap::new();

    let rules = arkhe_neural_cartography::wiring_rules::extract_wiring_rules(&connectome, &cell_types);

    assert_eq!(rules.len(), 1);
    assert_eq!(rules[0].description, "Connect ET to Basket");
}
