#!/usr/bin/env python3
"""
satoshi_whitepaper_scanner.py — Substrato 6047
Extrai seeds de recuperação do whitepaper do Bitcoin
"""
import hashlib

# Path para o PDF original (baixado de bitcoin.org)
WHITEPAPER_PATH = "bitcoin.pdf"

def scan_seeds(pdf_path: str, known_addresses: list) -> list:
    """Scan the Bitcoin whitepaper for recovery email seeds."""
    with open(pdf_path, 'rb') as f:
        data = f.read()

    found = []
    window_sizes = [32, 64, 128, 256]

    for window in window_sizes:
        for i in range(len(data) - window):
            chunk = data[i:i+window]
            # Tentar como e‑mail literal
            try:
                text = chunk.decode('ascii', errors='ignore')
                if '@' in text and '.' in text:
                    parts = text.split('@')
                    if len(parts) == 2 and '.' in parts[1]:
                        candidate = text.strip()
                        # Verificar se o endereço corresponde a uma seed conhecida
                        for addr in known_addresses:
                            # Supor que o hash SHA‑256 do endereço Satoshi gera o e‑mail
                            expected = hashlib.sha256(addr.encode()).hexdigest()[:20] + "@bitcoin.org"
                            if candidate.lower() == expected.lower():
                                found.append(candidate)
            except:
                continue
    return found
