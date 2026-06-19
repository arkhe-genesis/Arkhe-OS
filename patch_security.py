content = open('substrato-7001/src/webhooks/polar_handler.rs').read()

import re

# Constant time comparison via hmac slice comparison:
old_code = '''        // Use constant time comparison
        let expected_bytes = hex::decode(expected_str).unwrap_or_default();
        let computed_bytes = hex::decode(&computed).unwrap_or_default();
        if hmac::digest::crypto_common::Key::from_slice(&computed_bytes).ct_eq(
             hmac::digest::crypto_common::Key::from_slice(&expected_bytes)).into()
        {
            true
        } else {
            warn!("Assinatura inválida: computed={}, received={}", computed, expected_str);
            false
        } '''

new_code = '''        // Use constant time comparison
        let expected_bytes = hex::decode(expected_str).unwrap_or_default();
        let computed_bytes = hex::decode(&computed).unwrap_or_default();
        if expected_bytes.len() == computed_bytes.len() && expected_bytes.ct_eq(&computed_bytes).into()
        {
            true
        } else {
            warn!("Assinatura inválida: computed={}, received={}", computed, expected_str);
            false
        } '''

if old_code in content:
    content = content.replace(old_code, new_code)
    open('substrato-7001/src/webhooks/polar_handler.rs', 'w').write(content)
else:
    print("Code snippet not found for replacement!")
