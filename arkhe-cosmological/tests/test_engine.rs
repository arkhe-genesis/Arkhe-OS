use arkhe_cosmological::{
    CosmologicalEngine, InflationConfig,
};

#[test]
fn test_big_bang() {
    let mut cosmos = CosmologicalEngine::big_bang(InflationConfig::standard());
    cosmos.evolve(10); // 10 steps
    let dark_matter_density = cosmos.dark_information_density();
    assert!(dark_matter_density >= 0.0);
}
