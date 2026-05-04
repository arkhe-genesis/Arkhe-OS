pub struct WasmModule {
    pub functions: Vec<WasmFunction>,
}

pub struct WasmFunction {
    pub name: String,
    pub body: Vec<WasmInstruction>,
}

#[derive(Clone, Copy)]
pub enum WasmInstruction {
    I64Const(i64),
    I32Const(i32),
    EvmSstore,
    EvmSload,
    EvmKeccak256,
    EvmAddress,
    EvmTimestamp,
    EvmEmitLog { topics: u8 },
    I64Add,
    I64Sub,
    I64Mul,
    I64DivU,
    I64And,
    I64Or,
    I64Xor,
    Return,
}
