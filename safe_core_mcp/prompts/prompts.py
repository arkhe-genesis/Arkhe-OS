import json
import asyncio
from typing import Dict, Any, List

class MCPPrompt:
    def __init__(self, name: str, description: str, handler):
        self.name = name
        self.description = description
        self.handler = handler

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description
        }

    async def get(self, arguments: dict):
        return await self.handler(arguments)

def register_prompts(server) -> Dict[str, MCPPrompt]:
    prompts = {}

    async def security_audit(args: dict):
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Please perform a comprehensive security audit of the provided architecture. Focus on the 6 main threat categories and verify alignment with MA-S2 framework."
                }
            }
        ]

    async def vulnerability_analysis(args: dict):
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Analyze the provided code or configuration for vulnerabilities. Use the MA-S2 APM domain context to model attack paths and provide a risk score."
                }
            }
        ]

    async def compliance_report(args: dict):
        return [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": "Generate a compliance report based on the provided MA-S2 engine state. Ensure all domains (CVS, APM, INV, ARO) are evaluated."
                }
            }
        ]

    prompts["security_audit"] = MCPPrompt(
        name="security_audit",
        description="Template para auditoria completa de segurança",
        handler=security_audit
    )
    prompts["vulnerability_analysis"] = MCPPrompt(
        name="vulnerability_analysis",
        description="Template para análise de vulnerabilidade com MA-S2",
        handler=vulnerability_analysis
    )
    prompts["compliance_report"] = MCPPrompt(
        name="compliance_report",
        description="Template para geração de relatório de conformidade",
        handler=compliance_report
    )

    return prompts
