// substrates/v170_living_crystal/riscv_build.rs
/// Configuração de build para dispositivos RISC-V de baixa potência

/// Features específicas para RISC-V
#[cfg(target_arch = "riscv64")]
pub mod riscv_optimizations {
    use core::arch::asm;

    /// Instrução de contagem de população (acelera bit-shifting do NOMA)
    #[inline]
    pub fn popcount_u64(x: u64) -> u32 {
        unsafe {
            let result: u32;
            asm!("cpop {result}, {x}", x = in(reg) x, result = out(reg) result);
            result
        }
    }

    /// Multiplicação de ponto fixo com saturação (para coordenadas atômicas)
    #[inline]
    pub fn fixed_mul_sat(x: i32, y: i32, shift: u32) -> i32 {
        let result: i64 = (x as i64) * (y as i64);
        ((result >> shift) as i32).clamp(i32::MIN, i32::MAX)
    }
}

/// Configuração de memória para dispositivos embarcados
pub struct EmbeddedMemoryConfig {
    pub heap_size: usize,     // 64KB para IoT de baixa potência
    pub stack_size: usize,    // 32KB por thread
    pub dma_buffer: usize,    // Buffer para transferências SDR
}

impl Default for EmbeddedMemoryConfig {
    fn default() -> Self {
        Self {
            heap_size: 64 * 1024,
            stack_size: 32 * 1024,
            dma_buffer: 16 * 1024,
        }
    }
}
