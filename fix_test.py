import ast

with open("test_substrates.py", "r") as f:
    content = f.read()

lines = content.split('\n')
tree = ast.parse(content)

# Find functions named test_614_shieldnet
funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'test_614_shieldnet']

if len(funcs) > 1:
    # Remove the first occurrence
    func_to_remove = funcs[0]
    start = func_to_remove.lineno - 1
    end = func_to_remove.end_lineno

    del lines[start:end]

    with open("test_substrates.py", "w") as f:
        f.write('\n'.join(lines))
