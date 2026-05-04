fn main() {
    println!("cargo:rustc-link-lib=arkhe");
    println!("cargo:rustc-link-lib=z");
    println!("cargo:rustc-link-search=.");
}
