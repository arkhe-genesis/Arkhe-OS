use wasm_bindgen::prelude::*;
use serde::{Serialize, Deserialize};

#[wasm_bindgen]
#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
pub enum PhaseOpcode {
    SYNC = 0x01,         // SYNC - Synchronize local phase
    SYNC_K = 0x05,       // SYNC_K - Kuramoto global sync
    PROJ = 0x02,         // PROJ - Phase state projection (C -> Z)
    TZINOR_OPEN = 0x03,  // TZINOR_OPEN - Open retrocausal channel
    TZINOR_SEND = 0x04,  // TZINOR_SEND - Send phase packet
    TZINOR_CLOSE = 0x06, // TZINOR_CLOSE - Close channel
    LAMBDA_READ = 0x07,  // LAMBDA_READ - Read current coherence
    MEASURE_PSD = 0x08,  // MEASURE_PSD - Trigger interferometric analysis
    HALT = 0xFF,
}

#[wasm_bindgen]
pub struct PhaseVMWasm {
    pc: usize,
    stack: Vec<f64>,
    code: Vec<u8>,
    is_running: bool,
    lambda: f64,
    channels: Vec<bool>,
}

#[wasm_bindgen]
impl PhaseVMWasm {
    #[wasm_bindgen(constructor)]
    pub fn new() -> PhaseVMWasm {
        PhaseVMWasm {
            pc: 0,
            stack: Vec::with_capacity(256),
            code: Vec::new(),
            is_running: false,
            lambda: 0.999,
            channels: vec![false; 16],
        }
    }

    pub fn load_program(&mut self, code: &[u8]) {
        self.code = code.to_vec();
        self.pc = 0;
        self.is_running = true;
    }

    pub fn get_lambda(&self) -> f64 {
        self.lambda
    }

    pub fn run_next(&mut self) -> String {
        if !self.is_running || self.pc >= self.code.len() {
            return "IDLE: No program loaded or execution finished.".to_string();
        }

        let opcode = self.code[self.pc];
        self.pc += 1;

        match opcode {
            0x01 => "SYNC: Phase alignment established via Tzinor.".to_string(),
            0x05 => "SYNC_K: Kuramoto global coupling activated (K=5.0).".to_string(),
            0x02 => {
                self.lambda *= 1.0001;
                "PROJ: Phase state projected into structure (C -> Z).".to_string()
            },
            0x03 => {
                let ch = if self.pc < self.code.len() {
                    let id = self.code[self.pc] as usize % 16;
                    self.pc += 1;
                    self.channels[id] = true;
                    id
                } else { 0 };
                format!("TZINOR_OPEN: Retrocausal channel {} is now active.", ch)
            },
            0x04 => "TZINOR_SEND: Phase packet injected into the τ-field.".to_string(),
            0x06 => "TZINOR_CLOSE: Channel closure confirmed by JanusLock.".to_string(),
            0x07 => format!("LAMBDA_READ: Current coherence λ₂ = {:.4}", self.lambda),
            0x08 => "MEASURE_PSD: Identifying spacetime correlation class... Result: Class (b).".to_string(),
            0xFF => {
                self.is_running = false;
                "HALT: PhaseVM execution suspended.".to_string()
            },
            _ => format!("UNKNOWN: Phase distortion at PC 0x{:X} (Op: 0x{:02X}).", self.pc - 1, opcode),
        }
    }

    pub fn is_active(&self) -> bool {
        self.is_running
    }
}
