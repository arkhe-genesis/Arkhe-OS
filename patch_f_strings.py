import re

with open("substrates/t/1101_cathedral_qubes_integration/substrato_1101_cathedral_qubes_integration.py", "r") as f:
    content = f.read()

# Make sure we don't use f-strings in canonizer payload formatting
# although we just generated it with python f-strings, we need to check if there are any remaining.
# We wrote f'''import json ...''' in the bash script to generate the python script. So the python script itself shouldn't have f-strings.
print("f-string search:", re.findall(r'\bf(["\'])', content))
