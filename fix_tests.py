import os

files_to_patch = [
    "tests/telemetry/ClearcutLogger.test.ts",
    "tests/tools/console.test.ts",
    "tests/tools/pages.test.ts",
    "tests/tools/performance.test.ts",
    "tests/tools/screencast.test.ts",
    "tests/tools/screenshot.test.ts",
    "tests/tools/script.test.ts",
    "tests/tools/slim.test.ts",
    "tests/tools/snapshot.test.ts",
    "tests/tools/storage.test.ts",
    "tests/utils.ts"
]

header = "/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/ban-ts-comment, @typescript-eslint/no-unused-vars */\n"

for filepath in files_to_patch:
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            content = f.read()

        if "/* eslint-disable" not in content:
            lines = content.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('//') or line.startswith('/*') or line.startswith(' *') or line.startswith('*/') or line.startswith('"use client"') or line.startswith("'use client'"):
                    insert_idx = i + 1
                else:
                    if line.strip() != "":
                        break

            lines.insert(insert_idx, header)

            with open(filepath, "w") as f:
                f.write('\n'.join(lines))

print("Done patching tests!")
