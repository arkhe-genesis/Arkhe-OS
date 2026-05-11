use num_complex::Complex;

pub struct CNTConductivity {
    pub chiral: (u32, u32), // (m,0)
    pub radius: f64,
    pub chemical_potential: f64,
}

impl CNTConductivity {
    /// Calcula a condutividade zz(ω) e o fator de não‑localidade ξ(ω).
    pub fn evaluate(&self, omega: f64) -> (Complex<f64>, Complex<f64>) {
        let sigma_inter = self.interband_conductivity(omega);
        let sigma_intra = self.intraband_conductivity(omega);
        let sigma = sigma_inter + sigma_intra;
        let xi = Complex::new(1.0 / (2.0 * omega.powi(2)), 0.0) * self.second_derivative_q(omega);
        (sigma, xi)
    }

    fn interband_conductivity(&self, _omega: f64) -> Complex<f64> {
        Complex::new(0.0, 0.0)
    }

    fn intraband_conductivity(&self, _omega: f64) -> Complex<f64> {
        Complex::new(0.0, 0.0)
    }

    fn second_derivative_q(&self, _omega: f64) -> Complex<f64> {
        Complex::new(0.0, 0.0)
    }
}
