//! Defeitos de especificação registados no PACIR-Ω.

use crate::alpha::ALPHA_PACIR_OMEGA;

#[derive(Debug, Clone, PartialEq)]
pub struct SpecificationDefect {
    pub locus: String,
    pub declared: String,
    pub actual: f64,
    pub impact: String,
}

impl SpecificationDefect {
    /// Defeito do arXiv:2609.12146v1, Sec. III.3: "1/e ≈ 61%".
    pub fn article_threshold_defect() -> Self {
        Self {
            locus: "arXiv:2609.12146v1, Sec. III.3".into(),
            declared: "1/e ≈ 61%".into(),
            actual: ALPHA_PACIR_OMEGA,
            impact: format!(
                "Fator √e ≈ {:.4} sobre a região admissível e QUOPS scores",
                std::f64::consts::E.sqrt()
            ),
        }
    }

    /// Verifica se o defeito foi resolvido com a adoção de α = 1/√e.
    pub fn is_resolved(&self, adopted_alpha: f64) -> bool {
        (adopted_alpha - self.actual).abs() < 1e-12
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn defect_is_resolved_only_by_the_canonical_threshold() {
        let defect = SpecificationDefect::article_threshold_defect();
        assert_eq!(defect.declared, "1/e ≈ 61%");
        assert!(defect.is_resolved(ALPHA_PACIR_OMEGA));
        assert!(!defect.is_resolved(1.0 / std::f64::consts::E));
    }
}
