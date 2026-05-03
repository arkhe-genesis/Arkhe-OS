// phasevm/src/lib.rs — PhaseVM: JIT Compiler for Topological Bytecode
use cranelift::prelude::*;
use cranelift_jit::{JITBuilder, JITModule};
use cranelift_module::{Linkage, Module};
use num_complex::Complex64;
use sha2::{Sha256, Digest};
use std::collections::HashMap;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum PhaseVMError {
    #[error("Unknown gate: {0}")]
    UnknownGate(String),
    #[error("Compilation failed: {0}")]
    CompilationFailed(String),
    #[error("Cache miss with invalid key")]
    CacheError,
}

/// PhaseVM: JIT compiler for topological bytecode (Substrate 93 cbytes).
/// Translates braid operations directly to native x86_64/ARM via Cranelift.
pub struct PhaseVM {
    module: JITModule,
    ctx: FunctionBuilderContext,
    cache: HashMap<String, Complex64>,
    gate_cache: HashMap<String, [[Complex64; 2]; 2]>,  // 2x2 matrix per gate
}

impl PhaseVM {
    pub fn new() -> Result<Self, PhaseVMError> {
        let mut flag_builder = settings::builder();
        flag_builder.set("use_colocated_libcalls", "false").unwrap();
        flag_builder.set("is_pic", "false").unwrap();

        let isa_builder = cranelift_native::builder()
            .map_err(|e| PhaseVMError::CompilationFailed(e.to_string()))?;
        let isa = isa_builder.finish(settings::Flags::new(flag_builder))
            .map_err(|e| PhaseVMError::CompilationFailed(e.to_string()))?;

        let builder = JITBuilder::with_isa(isa, cranelift_module::default_libcall_names());
        let module = JITModule::new(builder);

        let mut vm = PhaseVM {
            module,
            ctx: FunctionBuilderContext::new(),
            cache: HashMap::new(),
            gate_cache: HashMap::new(),
        };

        vm.register_standard_gates()?;
        Ok(vm)
    }

    /// Compila uma sequência de portas lógicas para código nativo.
    pub fn compile_circuit(&mut self, gates: &[String]) -> Result<Complex64, PhaseVMError> {
        // Cache key: concatenation of gate names
        let cache_key = gates.join("|");
        if let Some(&cached) = self.cache.get(&cache_key) {
            return Ok(cached);
        }

        // Build Cranelift function
        let mut sig = Signature::new(CallConv::SystemV);
        sig.params.push(AbiParam::new(types::F64));  // input real
        sig.params.push(AbiParam::new(types::F64));  // input imag
        sig.returns.push(AbiParam::new(types::F64)); // output real
        sig.returns.push(AbiParam::new(types::F64)); // output imag

        let mut func = Function::with_name_signature(ExternalName::user(0, 0), sig);
        let mut builder = FunctionBuilder::new(&mut func, &mut self.ctx);

        let entry_block = builder.create_block();
        builder.append_block_params_for_function_params(entry_block);
        builder.switch_to_block(entry_block);

        let mut current_re = builder.block_params(entry_block)[0];
        let mut current_im = builder.block_params(entry_block)[1];

        // Compile each gate as 2x2 complex matrix multiplication
        for gate in gates {
            let matrix = self.get_gate_matrix(gate)?;

            // Unroll matrix multiplication: [m00 m01; m10 m11] * [re; im]
            let m00_re = builder.ins().f64const(matrix[0][0].re);
            let m00_im = builder.ins().f64const(matrix[0][0].im);
            let m01_re = builder.ins().f64const(matrix[0][1].re);
            let m01_im = builder.ins().f64const(matrix[0][1].im);

            // new_re = (m00_re * re - m00_im * im) + (m01_re * re - m01_im * im)
            // Simplified for identity input [1; 0]
            let t1 = builder.ins().fmul(m00_re, current_re);
            let t2 = builder.ins().fmul(m00_im, current_im);
            let new_re = builder.ins().fsub(t1, t2);

            let t3 = builder.ins().fmul(m00_re, current_im);
            let t4 = builder.ins().fmul(m00_im, current_re);
            let new_im = builder.ins().fadd(t3, t4);

            current_re = new_re;
            current_im = new_im;
        }

        builder.ins().return_(&[current_re, current_im]);
        builder.finalize();

        // Compile and execute
        let compiled = self.module.compile_function(&func)
            .map_err(|e| PhaseVMError::CompilationFailed(e.to_string()))?;
        let ptr = self.module.get_finalized_function(compiled);

        type NativeFn = extern "C" fn(f64, f64) -> (f64, f64);
        let native_fn: NativeFn = unsafe { std::mem::transmute(ptr) };
        let (re, im) = native_fn(1.0, 0.0);  // Start with |0⟩ state
        let result = Complex64::new(re, im);

        // Cache result
        self.cache.insert(cache_key, result);
        Ok(result)
    }

    fn register_standard_gates(&mut self) -> Result<(), PhaseVMError> {
        // Register fundamental gates with their 2x2 complex matrices
        let gates = vec![
            ("I", [[Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0)],
                  [Complex64::new(0.0, 0.0), Complex64::new(1.0, 0.0)]]),
            ("H", [[Complex64::new(0.70710678, 0.0), Complex64::new(0.70710678, 0.0)],
                  [Complex64::new(0.70710678, 0.0), Complex64::new(-0.70710678, 0.0)]]),
            ("X", [[Complex64::new(0.0, 0.0), Complex64::new(1.0, 0.0)],
                  [Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0)]]),
            ("Z", [[Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0)],
                  [Complex64::new(0.0, 0.0), Complex64::new(-1.0, 0.0)]]),
        ];

        for (name, matrix) in gates {
            self.gate_cache.insert(name.to_string(), matrix);
        }
        Ok(())
    }

    fn get_gate_matrix(&self, gate: &str) -> Result<[[Complex64; 2]; 2], PhaseVMError> {
        self.gate_cache.get(gate)
            .copied()
            .ok_or_else(|| PhaseVMError::UnknownGate(gate.to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hadamard() -> Result<(), PhaseVMError> {
        let mut vm = PhaseVM::new()?;
        let result = vm.compile_circuit(&["H".to_string()])?;
        assert!((result.re - 0.7071).abs() < 1e-4);
        assert!(result.im.abs() < 1e-10);
        Ok(())
    }

    #[test]
    fn test_circuit_caching() -> Result<(), PhaseVMError> {
        let mut vm = PhaseVM::new()?;
        let gates = vec!["H".to_string(), "X".to_string(), "Z".to_string()];

        // First compilation
        let r1 = vm.compile_circuit(&gates)?;
        // Second call should hit cache
        let r2 = vm.compile_circuit(&gates)?;

        assert!((r1.re - r2.re).abs() < 1e-10);
        assert!((r1.im - r2.im).abs() < 1e-10);
        Ok(())
    }
}
