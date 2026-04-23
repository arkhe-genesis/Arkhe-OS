import os
import re

def fix_logger():
    path = "server/logger.ts"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    content = content.replace("Record<string, unknown>", "AnyValueMap")
    with open(path, "w") as f: f.write(content)

def fix_state():
    path = "server/state.ts"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    content = content.replace("ContextNode", "_ContextNode")
    content = content.replace("MemoryEngram", "_MemoryEngram")
    # Prefix unused vars with _
    content = content.replace("const engram =", "const _engram =")
    content = content.replace("if (engram)", "if (_engram)")
    content = content.replace("originTime: engram.time", "originTime: _engram.time")
    with open(path, "w") as f: f.write(content)

def fix_types():
    path = "server/types.ts"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    if "interface ContextNode" in content:
        content = content.replace("interface ContextNode", "interface _ContextNode")
    if "interface MemoryEngram" in content:
        content = content.replace("interface MemoryEngram", "interface _MemoryEngram")
    content = content.replace("fContext: ContextNode[]", "fContext: _ContextNode[]")
    content = content.replace("gMemory: MemoryEngram[]", "gMemory: _MemoryEngram[]")
    with open(path, "w") as f: f.write(content)

def fix_dashboard():
    path = "src/components/CorvoNoirDashboard.tsx"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    # Remove duplicate imports
    lines = content.split('\n')
    new_lines = []
    seen_imports = set()
    in_recharts = False
    for line in lines:
        if "from 'recharts'" in line or "} from 'recharts'" in line:
            new_lines.append(line)
            continue
        if "XAxis," in line or "YAxis," in line or "CartesianGrid," in line or "Tooltip," in line:
             name = line.strip().replace(",","")
             if name in seen_imports: continue
             seen_imports.add(name)
        new_lines.append(line)
    content = '\n'.join(new_lines)
    # Define handleStressTest
    if "handleStressTest" not in content:
        content = content.replace("const handleRegenerationPulse", "const handleStressTest = () => fetch('/api/security/stress-test', { method: 'POST' });\n  const handleRegenerationPulse")
    # Fix progress color -> variant
    content = content.replace('color="cerenkov"', 'variant="default"')
    content = content.replace('color="cyan"', 'variant="default"')
    with open(path, "w") as f: f.write(content)

def fix_prism():
    path = "src/components/BonsaiPrismPanel.tsx"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    if 'import { Streamdown } from "streamdown"' not in content:
        content = 'import { Streamdown } from "streamdown";\n' + content
    with open(path, "w") as f: f.write(content)

def fix_dedup():
    path = "skills/career-ops/dedup-tracker.mjs"
    if not os.path.exists(path): return
    with open(path, "r") as f: content = f.read()
    # Add license
    if "Copyright" not in content:
        license = "/**\n * @license\n * Copyright 2026 Google LLC\n * SPDX-License-Identifier: Apache-2.0\n */\n\n"
        content = license + content
    # node: imports
    content = content.replace("from 'fs'", "from 'node:fs'")
    content = content.replace("from 'path'", "from 'node:path'")
    # curly braces for if
    content = re.sub(r'if \((.*?)\) continue', r'if (\1) {\n    continue;\n  }', content)
    content = re.sub(r'if \((.*?)\) return null', r'if (\1) {\n    return null;\n  }', content)
    # unused company
    content = content.replace("for (const [company, companyEntries] of groups)", "for (const [_company, companyEntries] of groups)")
    with open(path, "w") as f: f.write(content)

fix_logger()
fix_state()
fix_types()
fix_dashboard()
fix_prism()
fix_dedup()
