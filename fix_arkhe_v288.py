import re

with open('src/components/ArkheV288.tsx', 'r') as f:
    text = f.read()

# Webpack ignore doesn't work well for tsc without ts-ignore
text = text.replace(
    "const module = await import(/* @vite-ignore */ '/brainflow_wasm/brainflow.js');",
    "// @ts-ignore\n  const module = await import(/* @vite-ignore */ '/brainflow_wasm/brainflow.js?url');"
)

with open('src/components/ArkheV288.tsx', 'w') as f:
    f.write(text)
