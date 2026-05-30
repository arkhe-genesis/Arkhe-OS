import re

with open("substrates/t/989_passport_gateway/substrato_989_passport_gateway.py", "r") as f:
    content = f.read()

content = content.replace('    if not os.path.exists(toml_path):\n        with open(toml_path, "w") as f:\n            f.write("[substrate]\\nid = 989\\nname = \\"Passport Gateway\\"\\n")\n    if not os.path.exists(toml_path):\n        with open(toml_path, "w") as f:\n            f.write("[substrate]\\nid = 989\\nname = \\"Passport Gateway\\"\n")\n', '    if not os.path.exists(toml_path):\n        with open(toml_path, "w") as f:\n            f.write("[substrate]\\nid = 989\\nname = \\"Passport Gateway\\"\\n")\n')

with open("substrates/t/989_passport_gateway/substrato_989_passport_gateway.py", "w") as f:
    f.write(content)
