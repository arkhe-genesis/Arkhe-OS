#[derive(Debug)]
pub enum ArkheError {
    HumilityBelowGhost,
    TillingBelowGhost,
    Other(String),
}