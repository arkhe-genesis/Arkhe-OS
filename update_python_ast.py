import re

file_path = 'arkhe-polyglot-parser/arkhe_polyglot_parser.py'

with open(file_path, 'r') as f:
    content = f.read()

# Update NodeKind
content = content.replace(
    'ExprReturn = auto(); ExprThrow = auto(); ExprCast = auto(); ExprAssignment = auto()',
    'ExprReturn = auto(); ExprThrow = auto(); ExprCast = auto(); ExprAssignment = auto();\n    DeclTypeAlias = auto(); DeclTrait = auto()'
)

with open(file_path, 'w') as f:
    f.write(content)
