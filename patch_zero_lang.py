import sys

def patch_file():
    with open('polyglot/zero_lang_tool.py', 'r') as f:
        content = f.read()

    old_code = """
            # Integrar com Predictive Auto-Remediation (Substrato 223)
            if self.tool_system:
                # Avoid await error by passing it a request maybe?
                # Actually tool_system.invoke_tool uses ToolCallRequest
                # Since we don't have it here, let's assume it has an invoke_tool that takes a request
                # or just standard invoke_tool with parameters
                pass # Usually requires Request object, we'll ignore this for now
"""
    new_code = """
            # Integrar com Predictive Auto-Remediation (Substrato 223)
            if self.tool_system:
                from tool_calling.canonical_tool_system import ToolCallRequest
                import uuid
                await self.tool_system.invoke_tool(ToolCallRequest(
                    call_id=str(uuid.uuid4()),
                    tool_id="predictive_auto_remediation",
                    parameters={
                        "plan": plan,
                        "source": "zero_compiler",
                        "timestamp": time.time()
                    }
                ))
"""
    content = content.replace(old_code, new_code)

    with open('polyglot/zero_lang_tool.py', 'w') as f:
        f.write(content)

patch_file()
