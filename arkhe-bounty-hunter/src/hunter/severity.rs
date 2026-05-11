// ============================================================================
// ARKHE Bounty Hunter — Severity Classification
// ============================================================================
// CVSS v3.1 implementation with ARKHE-specific adjustments.
// Severity determines bounty priority and response urgency.
// ============================================================================

use std::cmp::Ordering;
use serde::{Serialize, Deserialize};

/// Vulnerability severity levels
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    /// CVSS 9.0-10.0 — Immediate action required
    Critical = 0,
    /// CVSS 7.0-8.9 — High priority
    High = 1,
    /// CVSS 4.0-6.9 — Standard priority
    Medium = 2,
    /// CVSS 0.1-3.9 — Low priority
    Low = 3,
    /// Informational findings
    Info = 4,
    /// Confirmed false positive (filtered)
    FalsePositive = 5,
}

impl Severity {
    pub fn from_cvss(score: f32) -> Self {
        if score >= 9.0 {
            Severity::Critical
        } else if score >= 7.0 {
            Severity::High
        } else if score >= 4.0 {
            Severity::Medium
        } else if score > 0.0 {
            Severity::Low
        } else {
            Severity::Info
        }
    }

    pub fn to_emoji(&self) -> &'static str {
        match self {
            Severity::Critical => "🔴",
            Severity::High => "🟠",
            Severity::Medium => "🟡",
            Severity::Low => "🟢",
            Severity::Info => "ℹ️",
            Severity::FalsePositive => "⚪",
        }
    }

    pub fn bounty_multiplier(&self) -> f32 {
        match self {
            Severity::Critical => 100.0,
            Severity::High => 50.0,
            Severity::Medium => 10.0,
            Severity::Low => 2.0,
            _ => 0.0,
        }
    }

    pub fn sla_hours(&self) -> u32 {
        match self {
            Severity::Critical => 4,
            Severity::High => 24,
            Severity::Medium => 72,
            Severity::Low => 30 * 24, // 30 days
            _ => u32::MAX,
        }
    }
}

impl Default for Severity {
    fn default() -> Self {
        Severity::Info
    }
}

impl std::fmt::Display for Severity {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Severity::Critical => write!(f, "Critical"),
            Severity::High => write!(f, "High"),
            Severity::Medium => write!(f, "Medium"),
            Severity::Low => write!(f, "Low"),
            Severity::Info => write!(f, "Info"),
            Severity::FalsePositive => write!(f, "False Positive"),
        }
    }
}

/// Classification interface
pub trait Classification {
    fn cvss_score(&self) -> f32;
    fn severity(&self) -> Severity;
}

/// CVSS v3.1 vector and calculation
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CVSSv3 {
    /// Attack Vector: Network (N), Adjacent (A), Local (L), Physical (P)
    pub attack_vector: AttackVector,
    /// Attack Complexity: Low (L), High (H)
    pub attack_complexity: AttackComplexity,
    /// Privileges Required: None (N), Low (L), High (H)
    pub privileges_required: PrivilegesRequired,
    /// User Interaction: None (N), Required (R)
    pub user_interaction: UserInteraction,
    /// Scope: Unchanged (U), Changed (C)
    pub scope: Scope,
    /// Confidentiality impact: None (N), Low (L), High (H)
    pub confidentiality_impact: Impact,
    /// Integrity impact: None (N), Low (L), High (H)
    pub integrity_impact: Impact,
    /// Availability impact: None (N), Low (L), High (H)
    pub availability_impact: Impact,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum AttackVector {
    Network,
    Adjacent,
    Local,
    Physical,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum AttackComplexity {
    Low,
    High,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PrivilegesRequired {
    None,
    Low,
    High,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum UserInteraction {
    None,
    Required,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Scope {
    Unchanged,
    Changed,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Impact {
    None,
    Low,
    High,
}

impl CVSSv3 {
    /// Calculate base score
    pub fn score(&self) -> f32 {
        let iss = self.impact_sub_score();
        let impact = if self.scope == Scope::Unchanged {
            6.42 * iss
        } else {
            7.52 * (iss - 0.029) - 3.25 * (iss - 0.02_f32.powf(15.0) - 0.029)
        };

        let exploitability = 8.22
            * self.attack_vector.multiplier()
            * self.attack_complexity.multiplier()
            * self.privileges_required.multiplier()
            * self.user_interaction.multiplier();

        let base = if impact <= 0.0 {
            0.0
        } else if self.scope == Scope::Unchanged {
            (impact + exploitability).round().min(10.0)
        } else {
            ((1.08_f32) * (impact + exploitability)).round().min(10.0)
        };

        base
    }

    fn impact_sub_score(&self) -> f32 {
        1.0 - (
            (1.0 - self.confidentiality_impact.multiplier())
            * (1.0 - self.integrity_impact.multiplier())
            * (1.0 - self.availability_impact.multiplier())
        )
    }
}

/// Classification of vulnerability class
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum VulnClass {
    Injection,
    BrokenAuth,
    SensitiveDataExposure,
    XXE,
    BrokenAccessControl,
    SecurityMisconfiguration,
    XSS,
    InsecureDeserialization,
    UsingComponentsWithKnownVulns,
    InsufficientLogging,
    SSRF,
    ServerSidePathTraversal,
    OSCommandInjection,
    WeakCryptography,
    HardcodedSecrets,
    RaceCondition,
    MemoryCorruption,
    LogicFlaw,
    Misconfiguration,
    DenialOfService,
}

impl VulnClass {
    pub fn bounty_base(&self) -> u32 {
        match self {
            VulnClass::Injection | VulnClass::OSCommandInjection => 5000,
            VulnClass::BrokenAuth | VulnClass::BrokenAccessControl => 3000,
            VulnClass::XXE | VulnClass::SSRF => 2500,
            VulnClass::MemoryCorruption | VulnClass::RaceCondition => 4000,
            VulnClass::InsecureDeserialization | VulnClass::WeakCryptography => 2000,
            VulnClass::HardcodedSecrets => 1500,
            VulnClass::LogicFlaw => 3500,
            VulnClass::DenialOfService => 1000,
            _ => 500,
        }
    }
}

impl Impact {
    fn multiplier(&self) -> f32 {
        match self {
            Impact::None => 0.0,
            Impact::Low => 0.56,
            Impact::High => 0.0, // High impact, different formula
        }
    }
}

impl AttackVector {
    fn multiplier(&self) -> f32 {
        match self {
            AttackVector::Network => 0.85,
            AttackVector::Adjacent => 0.62,
            AttackVector::Local => 0.55,
            AttackVector::Physical => 0.20,
        }
    }
}

impl AttackComplexity {
    fn multiplier(&self) -> f32 {
        match self {
            AttackComplexity::Low => 0.77,
            AttackComplexity::High => 0.44,
        }
    }
}

impl PrivilegesRequired {
    fn multiplier(&self) -> f32 {
        match self {
            PrivilegesRequired::None => 0.85,
            PrivilegesRequired::Low => 0.62,
            PrivilegesRequired::High => 0.27,
        }
    }
}

impl UserInteraction {
    fn multiplier(&self) -> f32 {
        match self {
            UserInteraction::None => 0.85,
            UserInteraction::Required => 0.62,
        }
    }
}

impl Scope {
    fn _multiplier(&self) -> f32 {
        match self {
            Scope::Unchanged => 1.0,
            Scope::Changed => 1.0, // Used in formula differently
        }
    }
}
