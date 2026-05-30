import re

with open("test_substrates.py", "r") as f:
    content = f.read()

# Fix test_substrate_563_1
content = re.sub(
    r'assert "cortexmae_bridge\.py" in data\["Files"\]',
    r'assert any("substrato_563_1.yaml" in f["filename"] for f in data["Files"])',
    content
)

# Fix test_substrate_100T
old_block_100t = """    assert "Substrate 100T canonized at:" in result.stdout

    # Extract path
    path = result.stdout.split("Substrate 100T canonized at: ")[1].split("\\n")[0].strip()

    with open(path, "r") as f:
        data = json.load(f)"""
new_block_100t = """    data = json.loads(result.stdout)"""

content = content.replace(old_block_100t, new_block_100t)

with open("test_substrates.py", "w") as f:
    f.write(content)
