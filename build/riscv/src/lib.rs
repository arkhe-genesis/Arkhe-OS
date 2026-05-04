// build/riscv/src/lib.rs — Entrypoint para dispositivos RISC-V IoT
#![no_std]
#![cfg_attr(not(test), no_main)]
#![feature(alloc_error_handler)]

extern crate alloc;

use core::panic::PanicInfo;
use alloc::boxed::Box;

// Importar orquestrador com features mínimas
use arkhe_unified::core::orchestrator::UnifiedOrchestrator;
use arkhe_unified::core::config::Config;

/// Entry point para RISC-V (chamado pelo runtime C)
#[no_mangle]
pub extern "C" fn arkhe_riscv_init(config_ptr: *const u8, config_len: usize) -> *mut UnifiedOrchestrator {
    // Parse configuração do buffer (simplificado)
    // Em produção: usar serde com allocator customizado para no_std
    let config_bytes = unsafe { core::slice::from_raw_parts(config_ptr, config_len) };

    // Em no_std, usar allocator global ou arena
    // Para exemplo: retornar null se falhar
    match Config::from_bytes(config_bytes) {
        Ok(config) => {
            match UnifiedOrchestrator::new_minimal(config) {
                Ok(orch) => Box::into_raw(Box::new(orch)),
                Err(_) => core::ptr::null_mut(),
            }
        }
        Err(_) => core::ptr::null_mut(),
    }
}

/// Executar missão no RISC-V (chamada assíncrona via callback)
#[no_mangle]
pub extern "C" fn arkhe_riscv_execute_mission(
    orch_ptr: *mut UnifiedOrchestrator,
    mission_id_ptr: *const u8,
    mission_id_len: usize,
    callback: extern "C" fn(result_ptr: *const u8, result_len: usize)
) {
    // Em produção: usar executor assíncrono no_std como embassy
    // Para exemplo: execução síncrona simplificada
    unsafe {
        if orch_ptr.is_null() {
            callback(core::ptr::null(), 0);
            return;
        }

        let orch = &mut *orch_ptr;
        let mission_id = core::str::from_utf8_unchecked(
            core::slice::from_raw_parts(mission_id_ptr, mission_id_len)
        );

        // Executar missão (simplificado para RISC-V)
        match orch.execute_mission_minimal(mission_id) {
            Ok(result) => {
                // Serializar resultado para buffer (simplificado)
                // let result_json = serde_json_core::to_string(&result).unwrap_or_else(|_| "error".into());
                let result_json = "{}"; // Dummy
                let result_ptr = result_json.as_ptr();
                let result_len = result_json.len();

                // Chamar callback com resultado
                callback(result_ptr, result_len);
            }
            Err(_) => callback(core::ptr::null(), 0),
        }
    }
}

/// Panic handler para no_std
#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    // Em produção: log para UART ou trigger watchdog reset
    loop {
        // WFI (Wait For Interrupt) para baixa potência em panic
        #[cfg(target_arch = "riscv64")]
        unsafe {
            core::arch::asm!("wfi");
        }
    }
}

/// Allocator error handler para no_std
#[alloc_error_handler]
fn alloc_error(_layout: core::alloc::Layout) -> ! {
    panic!("Allocation failed on RISC-V IoT device");
}

// Para builds com std (simulação/host)
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_riscv_init() {
        let config = Config::default();
        let config_bytes = b"{}";

        let orch_ptr = arkhe_riscv_init(config_bytes.as_ptr(), config_bytes.len());
        assert!(!orch_ptr.is_null());

        // Cleanup
        unsafe { drop(Box::from_raw(orch_ptr)); }
    }
}
