sed -i 's/tch = { version = "0.14.0", optional = true }/tch = { version = "0.19.0", optional = true }/g' arkhe-qart/substrate-6072/Cargo.toml
export LIBTORCH_USE_PYTORCH=1
export LIBTORCH_BYPASS_VERSION_CHECK=1
cd arkhe-qart/substrate-6072 && cargo check --features tch
