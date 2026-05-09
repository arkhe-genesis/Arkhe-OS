// build.rs — Script de pré-compilação para ARKHE OS v168
use std::env;
use std::fs;
use std::path::Path;
use std::process::Command;

fn main() {
    // Re-run if config changes
    println!("cargo:rerun-if-changed=config/");
    println!("cargo:rerun-if-changed=scripts/");

    // Generate version info
    let version = env::var("CARGO_PKG_VERSION").unwrap_or_else(|_| "0.0.0".into());
    let git_hash = get_git_hash().unwrap_or_else(|_| "unknown".into());
    let build_time = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();

    let version_info = format!(
        r#"pub const VERSION: &str = "{}";
pub const GIT_HASH: &str = "{}";
pub const BUILD_TIME: &str = "{}";
pub const TARGET: &str = "{}";
pub const FEATURES: &str = "{}";
"#,
        version,
        git_hash,
        build_time,
        env::var("TARGET").unwrap_or_else(|_| "unknown".into()),
        env::var("CARGO_FEATURES").unwrap_or_else(|_| "".into()),
    );

    let out_dir = env::var("OUT_DIR").unwrap();
    let dest_path = Path::new(&out_dir).join("version.rs");
    fs::write(&dest_path, version_info).unwrap();

    // Link quantum libraries if enabled
    if cfg!(feature = "quantum-hardware") {
        println!("cargo:rustc-link-lib=dylib=qiskit_c");
        println!("cargo:rustc-link-lib=dylib=pennylane");

        // Copy Python bindings if available
        if let Ok(py_lib_dir) = env::var("ARKHE_PYTHON_LIB_DIR") {
            println!("cargo:rustc-link-search=native={}", py_lib_dir);
        }
    }

    // Generate integrity manifest
    generate_integrity_manifest();

    // Pre-compile Python modules if using PyO3
    if cfg!(feature = "python-bindings") {
        precompile_python_modules();
    }

    // Emit cfg flags for conditional compilation
    println!("cargo:rustc-cfg=arkhe_unified");
    if cfg!(target_os = "linux") {
        println!("cargo:rustc-cfg=target_linux");
    }
    if cfg!(target_os = "macos") {
        println!("cargo:rustc-cfg=target_macos");
    }
    if cfg!(target_os = "windows") {
        println!("cargo:rustc-cfg=target_windows");
    }
}

fn get_git_hash() -> Result<String, Box<dyn std::error::Error>> {
    let output = Command::new("git")
        .args(&["rev-parse", "--short", "HEAD"])
        .output()?;

    if output.status.success() {
        Ok(String::from_utf8(output.stdout)?.trim().to_string())
    } else {
        Err("Failed to get git hash".into())
    }
}

fn generate_integrity_manifest() {
    use sha2::{Sha256, Digest};
    use std::collections::HashMap;

    let mut manifest = HashMap::new();

    // Hash all substrate source files
    let substrate_dir = Path::new("src/substrates");
    if substrate_dir.exists() {
        for entry in fs::read_dir(substrate_dir).unwrap() {
            let entry = entry.unwrap();
            let path = entry.path();
            if path.extension().map_or(false, |ext| ext == "rs") {
                let content = fs::read_to_string(&path).unwrap();
                let mut hasher = Sha256::new();
                hasher.update(content.as_bytes());
                let hash = format!("{:x}", hasher.finalize());
                manifest.insert(path.file_name().unwrap().to_string_lossy().into_owned(), hash);
            }
        }
    }

    // Write manifest to out dir
    let out_dir = env::var("OUT_DIR").unwrap();
    let manifest_path = Path::new(&out_dir).join("integrity_manifest.json");
    let manifest_json = serde_json::to_string_pretty(&manifest).unwrap();
    fs::write(&manifest_path, manifest_json).unwrap();

    println!("cargo:rerun-if-changed=src/substrates/");
}

fn precompile_python_modules() {
    // Use maturin or setuptools-rust to precompile Python extensions
    // This is a placeholder for the actual build logic
    println!("cargo:warning=Python module pre-compilation not fully implemented in build.rs");
}
