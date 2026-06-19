content = open('substrato-7001/Cargo.toml').read()
content = content.replace('webhooks = ["axum", "tower-http", "hmac", "sha2", "hex"]', 'webhooks = ["axum", "tower-http", "hmac", "sha2", "hex", "serde_json", "tokio"]')
open('substrato-7001/Cargo.toml', 'w').write(content)
