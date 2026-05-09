//! Ribozyme Computing — Catalytic RNA Processing
//!
//! Implements ribozyme-based molecular computation for the OrbVM.
//! Based on Cech, Altman, and Breaker research.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A ribozyme: catalytic RNA processor
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ribozyme {
    /// Unique identifier
    pub id: String,
    
    /// RNA sequence
    pub sequence: Vec<Nucleotide>,
    
    /// Ribozyme type
    pub ribozyme_type: RibozymeType,
    
    /// Catalytic rate (kcat)
    pub catalytic_rate: f64,
    
    /// Substrate specificity
    pub substrate: Substrate,
    
    /// Computational function
    pub function: ComputationalFunction,
    
    /// Coherence contribution
    pub coherence: f64,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum Nucleotide {
    A, U, G, C,
    // Modified nucleotides
    Psi,  // Pseudouridine
    m6A,  // N6-methyladenosine
    Ino,  // Inosine
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RibozymeType {
    /// Self-splicing group I intron
    GroupIIntron,
    /// Self-splicing group II intron
    GroupIIIntron,
    /// tRNA processing
    RNaseP,
    /// Self-cleaving
    Hammerhead,
    Hairpin,
    HDV,
    VS,
    /// Synthetic
    Artificial(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Substrate {
    /// RNA strand
    RNA(Vec<Nucleotide>),
    /// DNA strand
    DNA(Vec<char>),
    /// Small molecule
    SmallMolecule(String),
    /// Peptide
    Peptide(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ComputationalFunction {
    /// Logic gate
    LogicGate(LogicGate),
    /// Signal transduction
    Transducer,
    /// Memory element
    Memory,
    /// Sensor
    Sensor,
    /// Actuator
    Actuator,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum LogicGate {
    NOT,
    AND,
    OR,
    NAND,
    NOR,
    XOR,
    IMPLY,
}

impl Ribozyme {
    /// Create a hammerhead ribozyme logic gate
    pub fn hammerhead_not(target: &[Nucleotide]) -> Self {
        Self {
            id: format!("hh-{}", uuid::Uuid::new_v4()),
            sequence: Self::design_hammerhead(target),
            ribozyme_type: RibozymeType::Hammerhead,
            catalytic_rate: 1.0,
            substrate: Substrate::RNA(target.to_vec()),
            function: ComputationalFunction::LogicGate(LogicGate::NOT),
            coherence: 1.0,
        }
    }
    
    /// Design hammerhead sequence for target
    fn design_hammerhead(target: &[Nucleotide]) -> Vec<Nucleotide> {
        // Simplified: create hammerhead with target recognition arms
        let mut seq = vec![];
        
        // Stem I (5' recognition)
        seq.extend_from_slice(target);
        
        // Catalytic core (conserved)
        seq.extend_from_slice(&[
            Nucleotide::C, Nucleotide::U, Nucleotide::G,
            Nucleotide::A, Nucleotide::U, Nucleotide::G,
        ]);
        
        // Stem II (variable)
        seq.extend_from_slice(&[
            Nucleotide::G, Nucleotide::C, Nucleotide::G,
        ]);
        
        // Stem III (3' recognition)
        seq.extend_from_slice(target);
        
        seq
    }
    
    /// Execute ribozyme computation
    pub fn execute(&self, input: &[Nucleotide]) -> RibozymeResult {
        match &self.function {
            ComputationalFunction::LogicGate(gate) => {
                self.execute_logic(gate, input)
            }
            _ => RibozymeResult::PassThrough(input.to_vec()),
        }
    }
    
    fn execute_logic(&self, gate: &LogicGate, input: &[Nucleotide]) -> RibozymeResult {
        match gate {
            LogicGate::NOT => {
                // If input matches substrate, cleave (output = nothing)
                if self.matches_substrate(input) {
                    RibozymeResult::Cleaved
                } else {
                    RibozymeResult::PassThrough(input.to_vec())
                }
            }
            LogicGate::AND => {
                // Requires two inputs (simplified)
                RibozymeResult::PassThrough(input.to_vec())
            }
            _ => RibozymeResult::PassThrough(input.to_vec()),
        }
    }
    
    fn matches_substrate(&self, input: &[Nucleotide]) -> bool {
        if let Substrate::RNA(ref target) = self.substrate {
            input == target
        } else {
            false
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RibozymeResult {
    Cleaved,
    PassThrough(Vec<Nucleotide>),
    Ligatured(Vec<Nucleotide>),
    Modified(Vec<Nucleotide>),
}

/// Ribozyme processor manager
pub struct RibozymeProcessor {
    /// Active ribozymes
    ribozymes: Vec<Ribozyme>,
    
    /// Processing queue
    queue: Vec<Vec<Nucleotide>>,
    
    /// Output buffer
    output: Vec<RibozymeResult>,
    
    /// Coherence monitor
    coherence: f64,
}

impl RibozymeProcessor {
    pub fn new() -> Self {
        Self {
            ribozymes: vec![],
            queue: vec![],
            output: vec![],
            coherence: 1.618,
        }
    }
    
    /// Add ribozyme to processor
    pub fn add_ribozyme(&mut self, ribozyme: Ribozyme) {
        self.ribozymes.push(ribozyme);
    }
    
    /// Process input through ribozyme cascade
    pub fn process(&mut self, input: Vec<Nucleotide>) -> Vec<RibozymeResult> {
        let mut current = input;
        
        for ribozyme in &self.ribozymes {
            let result = ribozyme.execute(&current);
            self.output.push(result.clone());
            
            if let RibozymeResult::PassThrough(seq) = result {
                current = seq;
            } else {
                break;
            }
        }
        
        self.output.clone()
    }
}
