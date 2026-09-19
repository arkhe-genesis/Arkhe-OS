#!/ "prompt_integrity_scanner.py"
import os
import unicodedata
import hashlib

class PromptIntegrityScanner:
    DANGEROUS_CHARS = {
        '\u202e', '\u202d', '\u2066', '\u2067', '\u2068', '\u2069',
        '\u200b', '\u200c', '\u200d', '\u200e', '\u200f', '\u034f',
    }

    def scan_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        hidden = []
        for i, char in enumerate(content):
            if char in self.DANGEROUS_CHARS:
                hidden.append((i, hex(ord(char)), unicodedata.name(char, 'UNKNOWN')))
        if hidden:
            seal = hashlib.sha3_256(content.encode()).hexdigest()[:16]
            print("[CRÍTICO] Caracteres invisíveis em " + filepath + ": " + str(hidden) + ". Selo: " + seal)
            return False
        return True

if __name__ == "__main__":
    scanner = PromptIntegrityScanner()
    scanner.scan_file(".cursorrules")
