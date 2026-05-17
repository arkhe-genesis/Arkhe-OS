#!/usr/bin/env python3
"""
Arkhe OS - Substrato 214: Installer Cathedral
Integração do Inno Setup no Canonical Tool Calling System.
"""
import asyncio
import logging
from deployment.inno_setup_tool import InnoSetupTool

logging.basicConfig(level=logging.INFO)

async def main():
    print("ARKHE OS - Substrato 214: Installer Cathedral Active")
    inno = InnoSetupTool(compiler_path="/fake/path")

    script_content = inno.generate_script_template(
        app_name="ArkheOS_Node",
        version="v1.0.0",
        publisher="Arkhe",
        main_exe="arkhe_node.exe",
        output_dir="build",
    )
    print("\n📦 Script Inno Setup Gerado:")
    print(script_content)

    result = await inno.compile_installer(script_content, "ArkheOS_Node", "build", sign_with_hsm=False)
    print(f"\n📦 Resultado da Compilação: {result}")

if __name__ == "__main__":
    asyncio.run(main())
