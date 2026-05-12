pub mod pretense;
pub mod agi_behavior_templates;
pub mod mimetic_amplifier;
pub mod roleplay_shard;
pub mod temporal_consistency;

// Provide dummy task/ActionResult structs to make it compile independently,
// unless we pull it from elsewhere, but the issue shows the code depends on it
// and since it's a new crate, we can define them locally or import if a shared one exists.
pub struct Task;
pub struct ActionResult;
