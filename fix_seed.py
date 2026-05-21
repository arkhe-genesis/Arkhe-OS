import sys

filepath = 'substrates/300-399_foundations/substrato_393_calib_real/substrato_393_calib_real.py'
with open(filepath, 'r') as f:
    content = f.read()

new_content = content.replace("self.random_seed = 42", "self.random_seed = 42\n        random.seed(self.random_seed)")

with open(filepath, 'w') as f:
    f.write(new_content)
