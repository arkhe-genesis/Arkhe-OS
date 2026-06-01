import re

with open("test_substrates.py", "r") as f:
    content = f.read()

# I also noticed we are failing `test_substrato_846_enterprise_architecture_bridge` due to an error in `os.path.abspath`. Let's fix that.
content = content.replace("importlib.util.spec_from_file_location(\"substrato_846_enterprise_architecture_bridge\", file_path)", "importlib.util.spec_from_file_location(\"substrato_846_enterprise_architecture_bridge\", 'substrates/t/846_enterprise_architecture_bridge/substrato_846_enterprise_architecture_bridge.py')")

# also fix the other tests in test_substrates_f_strings_patch.py and test_substrates.py. I need to run pytest entirely to make sure everything passes.
with open("test_substrates.py", "w") as f:
    f.write(content)

