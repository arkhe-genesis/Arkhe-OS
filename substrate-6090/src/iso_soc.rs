use serde::{Serialize, Deserialize};

pub struct ISOSOCCompliance;

#[derive(Debug, Serialize, Deserialize)]
pub struct SecurityAudit;

#[derive(Debug, Serialize, Deserialize)]
pub struct SOC2Report;

#[derive(Debug, Serialize, Deserialize)]
pub struct AccessControlAudit;

#[derive(Debug, Serialize, Deserialize)]
pub struct EncryptionAudit;
