import os
import sys

def replace_imports(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".go"):
                path = os.path.join(root, file)
                with open(path, "r") as f:
                    content = f.read()

                new_content = content.replace('"arkhe.os/parser/frontends/api/', '"arkhe/parser/frontends/api/')
                new_content = new_content.replace('"arkhe.os/parser/lfir"', '"arkhe/parser/lfir"')

                if content != new_content:
                    with open(path, "w") as f:
                        f.write(new_content)
                    print(f"Fixed {path}")

replace_imports("arkhe-os/parser/frontends/api")
replace_imports("arkhe-os/cli")
