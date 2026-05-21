use arkhe_safe_core_sdk::fractal_wave::RoundlessValidator;

#[test]
fn test_roundless_consensus() {
    let mut v1 = RoundlessValidator::new("v1".to_string(), 0.88).unwrap();
    let v2 = RoundlessValidator::new("v2".to_string(), 0.88).unwrap();
    let v3 = RoundlessValidator::new("v3".to_string(), 0.88).unwrap();
    let v4 = RoundlessValidator::new("v4".to_string(), 0.88).unwrap();

    // Total peers: 4
    let mut w2 = v2.emit_wavelet(1000, 0.0);
    w2.state_hash = "STATE_A".to_string();

    let mut w3 = v3.emit_wavelet(1000, 0.0);
    w3.state_hash = "STATE_A".to_string();

    let mut w4 = v4.emit_wavelet(1000, 0.0);
    w4.state_hash = "STATE_A".to_string();

    v1.receive_wavelet(w2);
    v1.receive_wavelet(w3);
    v1.receive_wavelet(w4);

    // With 3 out of 4 (75%), maybe not enough for 76%. Let's add v1 itself.
    let mut w1 = v1.emit_wavelet(1000, 0.0);
    w1.state_hash = "STATE_A".to_string();
    v1.receive_wavelet(w1);

    // Now 4/4 agree
    let confirmed = v1.confirm_state(1000, 2000, 4);
    assert_eq!(confirmed, Some("STATE_A".to_string()));
}
