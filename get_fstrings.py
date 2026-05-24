import re
with open('substrates/600-699_advanced/substrato_612_llm_foundations/substrato_612_llm_foundations.py', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'(?<![A-Za-z0-9_])f["\']', text):
    print("Found at:", m.group(0))
