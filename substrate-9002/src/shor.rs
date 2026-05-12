use crate::vortex_driver::VortexQpu;
use rand::Rng;

/// Runs Shor's algorithm on the 3‑qubit vortex register to factor N.
/// Returns (factor1, factor2) on success.
pub async fn factor_with_vortex_qpu(
    qpu: &mut VortexQpu,
    n: u64,
    max_attempts: usize,
) -> Option<(u64, u64)> {
    // Only factor small numbers with 3 qubits (N < 2^6 = 64)
    if !(2..64).contains(&n) {
        return None;
    }

    // Choose a random coprime base 'a'
    let mut rng = rand::thread_rng();
    for _attempt in 0..max_attempts {
        let a = if n <= 2 { return None; } else { rng.gen_range(2..n) };
        let g = gcd(a, n);
        if g > 1 {
            // Found a factor by luck
            return Some((g, n / g));
        }

        // === Shor's algorithm ===
        // Step 1: Prepare equal superposition
        qpu.reset_all().await;
        for i in 0..3 {
            qpu.apply_hadamard(i).await.ok()?;
        }

        // Step 2: Modular exponentiation: |x⟩ → |x⟩|a^x mod N⟩
        // For 3‑qubit control (register size = 2^3 = 8), we need 8 values.
        // Implement controlled‑U^(2^j) gates with precomputed a^{2^j} mod N.
        let _modular_powers = (0..8).map(|e| mod_pow(a, e as u64, n)).collect::<Vec<_>>();

        for j in 0..3 {
            let power = mod_pow(a, 1 << j, n);
            qpu.apply_controlled_modular_mult(j, power, n).await.ok()?;
        }

        // Step 3: Inverse QFT (mirror of forward QFT)
        qpu.apply_inverse_qft().await.ok()?;

        // Step 4: Measure the output register
        let outcome = qpu.measure_all().await.ok()?;
        let m = outcome.iter().fold(0u64, |acc, &b| (acc << 1) | b as u64);

        // Step 5: Classical post‑processing
        if m == 0 {
            continue; // trivial period, try again
        }

        let q = 8; // number of states for 3 qubits
        let (r, success) = find_period(m, q);
        if !success || r % 2 != 0 {
            continue;
        }

        let candidate1 = gcd(mod_pow(a, r / 2, n) + 1, n);
        let candidate2 = gcd(mod_pow(a, r / 2, n) - 1, n);

        if candidate1 > 1 && candidate1 < n && n.is_multiple_of(candidate1) {
            return Some((candidate1, n / candidate1));
        }
        if candidate2 > 1 && candidate2 < n && n.is_multiple_of(candidate2) {
            return Some((candidate2, n / candidate2));
        }
    }

    None
}

/// For a measurement outcome m with Q possible states, find the period r.
fn find_period(m: u64, q: u64) -> (u64, bool) {
    // Simple continued fraction approximation of m/Q
    let frac = continued_fraction(m, q);
    // The denominator gives the period candidate
    for (_, denom) in frac {
        if denom > 0 && denom <= q {
            return (denom, true);
        }
    }
    (0, false)
}

/// Continued fraction expansion for rational m/Q
fn continued_fraction(m: u64, q: u64) -> Vec<(u64, u64)> {
    let mut a = m;
    let mut b = q;
    let mut cf = Vec::new();
    while b != 0 {
        let k = a / b;
        let r = a % b;
        cf.push((k, b));
        a = b;
        b = r;
    }
    cf
}

fn gcd(a: u64, b: u64) -> u64 {
    if b == 0 {
        a
    } else {
        gcd(b, a % b)
    }
}

fn mod_pow(base: u64, exp: u64, modulus: u64) -> u64 {
    let mut result = 1;
    let mut base = base % modulus;
    let mut exp = exp;
    while exp > 0 {
        if exp & 1 == 1 {
            result = (result * base) % modulus;
        }
        base = (base * base) % modulus;
        exp >>= 1;
    }
    result
}
