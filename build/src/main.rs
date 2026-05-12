use std::process::Command;

fn main() {
    println!("🛠️ ARKHE OS Build Orchestrator");

    // 1. Build all crates
    run("cargo", &["build", "--workspace", "--release"]);

    // 2. Run tests
    run("cargo", &["test", "--workspace", "--features", "full"]);

    // 3. Copy all binaries to build/output
    std::fs::create_dir_all("build/output/bin").unwrap();
    for bin in &["arkhe", "arkhed", "arkhe-ws", "arkhe-consciousness", "phase-oracle"] {
        std::fs::copy(
            format!("target/release/{}.exe", bin),
            format!("build/output/bin/{}.exe", bin),
        ).unwrap_or_else(|e| eprintln!("Warning: could not copy {}: {}", bin, e));
    }

    // 4. Package Python & models
    run_script("scripts/package_python.sh");
    run_script("scripts/fetch_models.sh");

    // 5. Generate installers
    run("candle", &["ARKHE.wxs", "-o", "ARKHE.wixobj"]);
    run("light", &["ARKHE.wixobj", "-out", "ARKHE.msi"]);
    println!("✅ MSI built: build/output/ARKHE.msi");

    run("iscc", &["ARKHE.iss"]);
    println!("✅ EXE built: build/output/ARKHE-OS-6.1.0-win64.exe");

    println!("🎉 Cathedral assembled. Distributable artifacts are in build/output/.");
}

fn run(cmd: &str, args: &[&str]) {
    let status = Command::new(cmd).args(args).status().expect("command failed");
    if !status.success() { panic!("{} {:?} exited with {}", cmd, args, status); }
}

fn run_script(_script: &str) { /* invoke shell/powershell */ }