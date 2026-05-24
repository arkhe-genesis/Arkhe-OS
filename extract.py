import sys
import base64
import re

def extract(py_file, out_file):
    with open(py_file, "r") as f:
        content = f.read()
    match = re.search(r'b64_content = "(.*?)"', content)
    if match:
        with open(out_file, "wb") as f:
            f.write(base64.b64decode(match.group(1)))
        print(f"Extracted to {out_file}")

extract("substrates/680-PVAC-CRYPTO/substrato_680_pvac_crypto.py", "680.rs")
extract("substrates/681-PVAC-FHE/substrato_681_pvac_fhe.py", "681.rs")
extract("substrates/682-PVAC-NET/substrato_682_pvac_net.py", "682.rs")
