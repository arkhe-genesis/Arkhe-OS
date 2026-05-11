use clap::Parser;
use crate::{load_proof, RegulatoryConfig};

#[derive(Parser)]
pub struct RegulatoryVerifierArgs {
    #[arg(long)]
    pub proof_path: String,      // path to serialised CoherenceProof
    #[arg(long, default_value = "0.999")]
    pub min_coverage: f64,
}

pub fn main_verifier(args: RegulatoryVerifierArgs) {
    let proof = load_proof(&args.proof_path);
    let config = RegulatoryConfig { min_coverage: args.min_coverage };
    match proof.verify_for_regulator(&config) {
        Ok(report) => println!("✅ Therapeutic thoroughness certified.\n{}", report),
        Err(e) => println!("❌ Certification failed: {}", e),
    }
}
