use std::time::{SystemTime, UNIX_EPOCH};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("Time went backwards")
        .as_secs();

    // Mock output for the TLSNotary proof
    println!(r#"{{"session_id": "mock_session_42", "timestamp": {}, "server_cert": "mock_cert"}}"#, timestamp);
}
