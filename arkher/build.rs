fn main() {
    println!("cargo:rustc-link-search=..");
    println!("cargo:rustc-link-lib=arkhe");
    println!("cargo:rustc-link-lib=z");
}
