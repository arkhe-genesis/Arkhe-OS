import re

with open("node/PassportEmbed.jsx", "r") as f:
    content = f.read()

replacement1 = """
      // 1. Verificar humanidade via Passport Gateway (989.x)
      const humanityRes = await fetch(
        `${apiBaseUrl}/identity/passport?address=${encodeURIComponent(address)}${orcidId ? `&orcid_id=${encodeURIComponent(orcidId)}` : ''}`
      );
"""
content = re.sub(r'      // 1\. Verificar humanidade via Passport Gateway \(989\.x\).*?\);\n', replacement1.lstrip(), content, flags=re.DOTALL)

replacement2 = """
      // 2. Verificar Proof of Clean Hands (989.x.1)
      const cleanHandsRes = await fetch(
        `${apiBaseUrl}/clean-hands/check?address=${encodeURIComponent(address)}`
      );
"""
content = re.sub(r'      // 2\. Verificar Proof of Clean Hands \(989\.x\.1\).*?\);\n', replacement2.lstrip(), content, flags=re.DOTALL)

replacement3 = """
      // 3. Verificar se pode votar na DAO (979)
      const daoRes = await fetch(
        `${apiBaseUrl}/dao/verify-voter?address=${encodeURIComponent(address)}`
      );
"""
content = re.sub(r'      // 3\. Verificar se pode votar na DAO \(979\).*?\);\n', replacement3.lstrip(), content, flags=re.DOTALL)

with open("node/PassportEmbed.jsx", "w") as f:
    f.write(content)
