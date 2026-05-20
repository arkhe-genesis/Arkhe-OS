use criterion::{criterion_group, criterion_main, Criterion};

fn criterion_benchmark(c: &mut Criterion) {
    // Empty benchmark for now
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
