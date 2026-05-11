use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ComplianceBlock;

#[derive(Debug, Serialize, Deserialize)]
pub struct ComplianceEvent;

pub fn anchor_compliance_event() {}
