with open("node/tests/test_passport_gateway.py", "r") as f:
    content = f.read()

# Add the test runner at the very end if it is missing
if "if __name__ == \"__main__\":" not in content:
    content += "\nif __name__ == \"__main__\":\n    pytest.main([__file__, \"-v\", \"--tb=short\"])\n"

with open("node/tests/test_passport_gateway.py", "w") as f:
    f.write(content)
