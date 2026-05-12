use std::env;

fn main() {
    let dir = env::var("CARGO_MANIFEST_DIR").unwrap();
    println!(
        "cargo:rustc-link-search=native={}/../third_party/leveldb/build",
        dir
    );
    println!("cargo:rustc-link-lib=static=leveldb");
    // Link C++ standard library as LevelDB is written in C++
    println!("cargo:rustc-link-lib=stdc++");
}
