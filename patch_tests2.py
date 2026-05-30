with open("test_substrates.py", "r") as f:
    content = f.read()

content = content.replace('    assert "passport_gateway.py" in report["Files"]\n    assert "desci_nodes_bridge.py" in report["Files"]\n', '    assert "passport_gateway.py" in report["Files"]\n    assert "desci_nodes_bridge.py" in report["Files"]\n    assert "distributed_cache.py" in report["Files"]\n    assert "proof_of_clean_hands.py" in report["Files"]\n    assert "temporal_chain_anchor.py" in report["Files"]\n    assert "PassportEmbed.jsx" in report["Files"]\n')

with open("test_substrates.py", "w") as f:
    f.write(content)
