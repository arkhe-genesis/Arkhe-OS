#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: Zero Language Canonization
Registra o Zero como linguagem nativa de agentes na Catedral.
"""

import asyncio
import json
import sys
import os

# Add root directory to path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from polyglot.zero_lang_tool import ZeroLangTool
from tool_calling.canonical_tool_system import CanonicalToolCallingSystem

async def main():
    print("=" * 80)
    print("ARKHE Ω-TEMP v∞.Ω — SUBSTRATO ∞: ZERO LANG CANONIZATION")
    print("Canonizing zero-lang as a Cathedral citizen")
    print("=" * 80)

    # Initialize the canonical tool system
    tool_system = CanonicalToolCallingSystem()

    # Initialize the ZeroLangTool
    zero_tool = ZeroLangTool(tool_system=tool_system)

    # Register all tools
    registered_count = zero_tool.register_all_tools(tool_system)

    print(f"\n[Canonization Complete] {registered_count} tools registered.")

    for tool_id in tool_system.tool_registry.keys():
        print(f" - {tool_id}")

    print("\n" + "=" * 80)
    print("✅ SUBSTRATO ∞: ZERO_LANG_CANONIZED_COMPLETE")
    print("CANONICAL SEAL: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
