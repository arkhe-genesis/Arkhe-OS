import base64
import os

with open("goose_cathedral_bridge.py", "rb") as f:
    content = f.read()

b64_content = base64.b64encode(content).decode("utf-8")

with open("substrates/t/1077_goose_cathedral_bridge/goose_cathedral_bridge.b64", "w") as f:
    f.write(b64_content)
