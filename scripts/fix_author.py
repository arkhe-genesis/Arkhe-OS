import re

with open("skills/software-copyright-materials/SKILL.md", "r") as f:
    content = f.read()

new_content = re.sub(
    r"(metadata:\s*\n\s*short-description:.*)",
    r"\1\n  author: Rafael Oliveira (ORCID: 0009-0005-2697-4668)",
    content
)

with open("skills/software-copyright-materials/SKILL.md", "w") as f:
    f.write(new_content)
