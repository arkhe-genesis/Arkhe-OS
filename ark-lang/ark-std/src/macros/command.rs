#[macro_export]
macro_rules! command_capture {
    ($cmd:expr) => {{
        // Implementation
        Ok(String::from("captured"))
    }};
}
