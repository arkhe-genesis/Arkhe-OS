use std::env;
use std::path::PathBuf;

fn main() {
    let dir = env::current_dir().unwrap();
    let proto_path = dir.parent().unwrap().parent().unwrap().join("oracle-server").join("proto").join("oracle.proto");
    let proto_dir = dir.parent().unwrap().parent().unwrap().join("oracle-server").join("proto");

    tonic_build::configure()
        .compile_protos(&[proto_path], &[proto_dir])
        .unwrap();
}
