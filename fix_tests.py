import re

with open("test_substrates.py", "r") as f:
    content = f.read()

# Find the start of the first test_substrato_807_arkhe_runtime definition
match1 = re.search(r'def test_substrato_807_arkhe_runtime\(\):', content)
if match1:
    # Find the start of the second one
    match2 = re.search(r'def test_substrato_807_arkhe_runtime\(\):', content[match1.end():])
    if match2:
        print("Found duplicate test!")
        # We need to remove the second one. Since it was appended, let's just find the last index and cut it
        last_index = content.rfind("def test_substrato_807_arkhe_runtime():")
        new_content = content[:last_index]
        with open("test_substrates.py", "w") as f:
            f.write(new_content)
        print("Fixed duplicate test.")
    else:
        print("No duplicate test found.")
else:
    print("Test not found at all.")
