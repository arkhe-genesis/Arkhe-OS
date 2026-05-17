with open("orchestration/universal_orchestrator.py", "r") as f:
    content = f.read()

# Make sure we don't have multiple imports
if "from substrato_214_installer_cathedral import InnoSetupTool" not in content:
    content = content.replace("from enum import Enum", "from enum import Enum\nfrom substrato_214_installer_cathedral import InnoSetupTool")

# Update initialization
if "self.deployment = InnoSetupTool" not in content:
    content = content.replace(
        "self.observability = ArkheObservability()",
        "self.observability = ArkheObservability()\n\n        # Inicializar δ‑mem e tool system\n        self.delta_mem = ArkheDeltaMemoryWrapper(backbone_model=None)  # backbone real injetado depois\n        self.deployment = InnoSetupTool(temporal=temporal_chain, delta_mem=self.delta_mem)"
    )

content = content.replace("        self.delta_mem = ArkheDeltaMemoryWrapper(backbone_model=None)  # backbone real injetado depois\n", "")

# Add tools if not added
if "deployment_compile_installer" not in content:
    content = content.replace(
        "def _register_all_tools(self):",
        """def _register_all_tools(self):
        \"\"\"Registra cada operação de domínio como uma ferramenta idempotente e segura.\"\"\"
        # Deployment (Substrato 214)
        self.tool_system.register_tool(ToolDefinition(
            tool_id="deployment_compile_installer",
            name="Compile Installer",
            description="Compila instalador Windows via Inno Setup",
            handler=self.deployment.compile_installer,
            agent_owner="deployment_sentinel",
            confidence_required=0.85,
            token_cost_estimate=50,
            idempotent=True,
            max_concurrent=1
        ))
        self.tool_system.register_tool(ToolDefinition(
            tool_id="deployment_generate_iss_template",
            name="Generate ISS Template",
            description="Gera script .iss para compilação",
            handler=self.deployment.generate_iss_template,
            agent_owner="deployment_sentinel",
            confidence_required=0.7,
            token_cost_estimate=5
        ))"""
    )
    # Remove the old docstring if it was there since we replaced it with the function signature
    content = content.replace("        \"\"\"Registra cada operação de domínio como uma ferramenta idempotente e segura.\"\"\"\n\n        # Segurança", "        # Segurança")

# Add DEPLOYMENT enum
if "DEPLOYMENT = \"deployment\"" not in content:
    content = content.replace("BUSINESS = \"business\"", "BUSINESS = \"business\"\n    DEPLOYMENT = \"deployment\"")

with open("orchestration/universal_orchestrator.py", "w") as f:
    f.write(content)
