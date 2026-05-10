// Integration tests no WasmEdge / Wasmer
// This file contains tests that are meant to be compiled to WASM and run on WasmEdge/Wasmer

// ============================================================================
// HOW TO TEST ON WASMER / WASMEDGE
// ============================================================================
// WasmEdge is a lightweight, high-performance, and extensible WebAssembly runtime.
// Wasmer is a fast and secure WebAssembly runtime that enables lightweight containers.
//
// 1. Build the tests for WASI target:
//    cargo build --target wasm32-wasi --tests
//
// 2. Run with Wasmer:
//    wasmer run target/wasm32-wasi/debug/deps/integration-*.wasm
//
// 3. Run with WasmEdge:
//    wasmedge target/wasm32-wasi/debug/deps/integration-*.wasm
//
// Note: If you don't have WASI target installed, run:
//    rustup target add wasm32-wasi
// ============================================================================

use arkhe_wasm::core::temporal::Fixed;
use arkhe_wasm::acl::AclCompiler;

#[test]
fn test_fixed_point_arithmetic() {
    let a = Fixed::from_int(2);
    let b = Fixed::from_float(0.5);
    let c = a.mul(b);
    assert_eq!(c.0, Fixed::ONE.0); // 2 * 0.5 = 1.0

    // Testing boundary conditions
    let zero = Fixed::ZERO;
    assert_eq!(a.mul(zero).0, 0);
}

#[test]
fn test_acl_compiler_to_wasm() {
    let compiler = AclCompiler::new();
    let wasm = compiler.compile_to_wasm("contract p => q").unwrap();
    assert_eq!(&wasm[0..4], &[0x00, 0x61, 0x73, 0x6D]); // WASM magic header \0asm
    assert_eq!(&wasm[4..8], &[0x01, 0x00, 0x00, 0x00]); // version 1
}

#[test]
fn test_acl_compiler_error_handling() {
    let compiler = AclCompiler::new();
    let res = compiler.compile_to_wasm("contract with error => fail");
    assert!(res.is_err());
}
