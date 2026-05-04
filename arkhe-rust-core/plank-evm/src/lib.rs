use ethnum::u256;
use std::collections::HashMap;
use plank_wasm::{WasmFunction, WasmInstruction};

pub enum EvmOpcode {
    Stop = 0x00,
    Add = 0x01,
    Mul = 0x02,
    Sub = 0x03,
    Div = 0x04,
    Sload = 0x54,
    Sstore = 0x55,
    Push1 = 0x60,
    Push2 = 0x61,
    Push8 = 0x67,
    Push32 = 0x7F,
    Return = 0xF3,
    Address = 0x30,
    Timestamp = 0x42,
    Keccak256 = 0x20,
    Log0 = 0xA0,
}

pub struct EvmCodegen {
    pub bytecode: Vec<u8>,
}

impl EvmCodegen {
    pub fn new() -> Self {
        Self { bytecode: Vec::new() }
    }

    pub fn emit_push(&mut self, value: u256) {
        if value == u256::ZERO {
            self.bytecode.push(EvmOpcode::Push1 as u8);
            self.bytecode.push(0x00);
        } else if value <= u256::from(0xFFu64) {
            self.bytecode.push(EvmOpcode::Push1 as u8);
            self.bytecode.push(value.as_u8());
        } else if value <= u256::from(0xFFFFu64) {
            self.bytecode.push(EvmOpcode::Push2 as u8);
            self.bytecode.extend_from_slice(&value.as_u16().to_be_bytes());
        } else if value <= u256::from(u64::MAX) {
            self.bytecode.push(EvmOpcode::Push8 as u8);
            self.bytecode.extend_from_slice(&value.as_u64().to_be_bytes());
        } else {
            self.bytecode.push(EvmOpcode::Push32 as u8);
            let bytes = value.to_be_bytes();
            self.bytecode.extend_from_slice(&bytes);
        }
    }

    pub fn compile_function(&mut self, func: &WasmFunction) {
        for instr in &func.body {
            match instr {
                WasmInstruction::I64Const(v) => self.emit_push(u256::from(*v as u64)),
                WasmInstruction::I32Const(v) => self.emit_push(u256::from(*v as u32)),
                WasmInstruction::EvmSstore => self.bytecode.push(EvmOpcode::Sstore as u8),
                WasmInstruction::EvmSload => self.bytecode.push(EvmOpcode::Sload as u8),
                WasmInstruction::EvmKeccak256 => self.bytecode.push(EvmOpcode::Keccak256 as u8),
                WasmInstruction::EvmAddress => self.bytecode.push(EvmOpcode::Address as u8),
                WasmInstruction::EvmTimestamp => self.bytecode.push(EvmOpcode::Timestamp as u8),
                WasmInstruction::EvmEmitLog { topics } => {
                    self.bytecode.push(EvmOpcode::Log0 as u8 + *topics);
                }
                WasmInstruction::I64Add => self.bytecode.push(EvmOpcode::Add as u8),
                WasmInstruction::I64Sub => self.bytecode.push(EvmOpcode::Sub as u8),
                WasmInstruction::I64Mul => self.bytecode.push(EvmOpcode::Mul as u8),
                WasmInstruction::I64DivU => self.bytecode.push(EvmOpcode::Div as u8),
                WasmInstruction::Return => self.bytecode.push(EvmOpcode::Return as u8),
                _ => {}
            }
        }
    }

    pub fn finalize(self) -> Vec<u8> {
        self.bytecode
    }
}
