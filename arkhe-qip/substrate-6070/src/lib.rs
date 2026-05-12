// Substrate 6070 - The Entropy Oracle
pub fn shannon_entropy(data: &[u8]) -> f64 {
    if data.is_empty() {
        return 0.0;
    }
    let mut counts = [0usize; 256];
    for &b in data {
        counts[b as usize] += 1;
    }
    let mut entropy = 0.0;
    let len = data.len() as f64;
    for &count in &counts {
        if count > 0 {
            let p = count as f64 / len;
            entropy -= p * p.log2();
        }
    }
    entropy
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_entropy() {
        assert_eq!(shannon_entropy(b""), 0.0);
        let e = shannon_entropy(b"0000");
        assert_eq!(e, 0.0);
    }
}
