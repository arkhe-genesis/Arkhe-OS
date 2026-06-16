import os
import re

def patch_file(path):
    with open(path, 'r') as f:
        content = f.read()

    # Matches f"..." and f'...'
    pattern = re.compile(r'f([\'"])(.*?)\1')

    def replacer(match):
        quote = match.group(1)
        inner = match.group(2)

        # very basic translation for `{var}` into `.format(var=var)`
        # this won't perfectly handle complex expressions but it's okay for basic stuff
        if '{' in inner and '}' in inner:
            vars_found = re.findall(r'\{(.*?)\}', inner)
            format_str = quote + inner + quote + '.format(' + ', '.join([f'{v}={v}' for v in vars_found]) + ')'
            return format_str
        return quote + inner + quote

    new_content = pattern.sub(replacer, content)

    if new_content != content:
        with open(path, 'w') as f:
            f.write(new_content)
        print(f"Patched {path}")

for root, _, files in os.walk('cathedral-llm-agent'):
    for file in files:
        if file.endswith('.py'):
            patch_file(os.path.join(root, file))
