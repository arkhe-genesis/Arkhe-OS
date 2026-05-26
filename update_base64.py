import base64
import os

with open('substrates/t/846_enterprise_architecture_bridge/substrato_846_enterprise_architecture_bridge.py', 'r') as f:
    content = f.read()

import re

# find base64 string
match = re.search(r'"code_base64": "([^"]+)"', content)
b64 = match.group(1)

decoded = base64.b64decode(b64).decode('utf-8')
decoded = decoded.replace('cell = "846-SYS-FUNC"', 'cell = "846-SYST-HOW"')

encoded = base64.b64encode(decoded.encode('utf-8')).decode('utf-8')

new_content = content.replace(b64, encoded)

with open('substrates/t/846_enterprise_architecture_bridge/substrato_846_enterprise_architecture_bridge.py', 'w') as f:
    f.write(new_content)
