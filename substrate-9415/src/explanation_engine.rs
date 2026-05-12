use crate::risk_entropy::RiskLevel;

pub struct ExplanationEngine;

impl ExplanationEngine {
    pub fn explain_apy(apy: f64) -> String {
        format!("Se você depositar R$ 1.000 hoje, em um ano poderá ter cerca de R$ {:.0}, MAS esse valor muda diariamente.", 1000.0 * (1.0 + apy/100.0))
    }

    pub fn explain_risk(level: &RiskLevel, entropy: f64) -> String {
        match level {
            RiskLevel::Baixo => format!("Este pool tem oscilações baixas (Entropia: {:.1} bits).", entropy),
            RiskLevel::Moderado => format!("Risco moderado (Entropia: {:.1} bits). Oscilações esperadas.", entropy),
            RiskLevel::Alto => format!("Este pool teve altas oscilações (Entropia: {:.1} bits). Em uma semana ruim você pode perder 10% do seu dinheiro.", entropy),
            RiskLevel::Extremo => format!("Risco Extremo (Entropia: {:.1} bits). Você pode perder todo o dinheiro rapidamente.", entropy),
        }
    }

    pub fn explain_liquidity(tvl: f64) -> String {
        if tvl > 1_000_000.0 {
            format!("Há R$ {:.1} milhões bloqueados aqui. Alta liquidez.", tvl / 1_000_000.0)
        } else {
            format!("Há R$ {:.2} mil bloqueados aqui. Baixa liquidez, cuidado com a concentração.", tvl / 1000.0)
        }
    }
}
