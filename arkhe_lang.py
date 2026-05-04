# arkhe_lang.py — Compilador de intenções para a Catedral

import re
import json
from typing import Dict, List, Any, Optional

class ArkheIntentAST(dict):
    """
    Representação da AST de uma intenção em arkhe-lang.
    """
    @property
    def valid(self) -> bool:
        return "name" in self

    @property
    def error(self) -> Optional[str]:
        if not self.valid:
            return "Nome do protocolo não encontrado (ex: protocol \"Nome\" { ... })"
        return None

def compile(intention_code: str) -> ArkheIntentAST:
    """
    Compila uma intenção escrita em arkhe-lang para uma estrutura de dados (AST).
    Utiliza regex aprimorado para capturar blocos e parâmetros.
    """
    ast = ArkheIntentAST()

    # Limpar comentários de linha
    clean_code = re.sub(r'//.*', '', intention_code)

    # Extrair nome do protocolo
    name_match = re.search(r'protocol\s+"([^"]+)"', clean_code)
    if name_match:
        ast["name"] = name_match.group(1)

    # Extrair descrição
    desc_match = re.search(r'description:\s*"([^"]+)"', clean_code)
    if desc_match:
        ast["description"] = desc_match.group(1)

    # Extrair entidades
    entities_match = re.search(r'entities:\s*\[(.*?)\]', clean_code, re.DOTALL)
    if entities_match:
        entities_raw = entities_match.group(1)
        ast["entities"] = [e.strip() for e in entities_raw.split(',') if e.strip()]

    # Extrair privacidade
    privacy_block_match = re.search(r'privacy:\s*\{(.*?)\n\s*\}', clean_code, re.DOTALL)
    if privacy_block_match:
        privacy_raw = privacy_block_match.group(1)
        privacy_data = {}
        # Encontra sub-blocos de entidades
        entity_blocks = re.findall(r'(\w+):\s*\{(.*?)\}', privacy_raw, re.DOTALL)
        for entity, content in entity_blocks:
            details = {}
            # Busca pares chave: valor dentro do bloco
            pairs = re.findall(r'(\w+):\s*([^,\n}]+)', content)
            for k, v in pairs:
                val = v.strip().replace('"', '')
                try:
                    # Tenta converter para float se possível
                    if '.' in val:
                        val = float(val)
                    elif val.isdigit():
                        val = int(val)
                except ValueError:
                    pass
                details[k] = val
            privacy_data[entity] = details
        ast["privacy"] = privacy_data

    # Extrair consenso
    consensus_block_match = re.search(r'consensus:\s*\{(.*?)\}', clean_code, re.DOTALL)
    if consensus_block_match:
        consensus_raw = consensus_block_match.group(1)
        consensus_data = {}
        pairs = re.findall(r'(\w+):\s*([^,\n}]+)', consensus_raw)
        for k, v in pairs:
            val = v.strip().replace('"', '')
            if '/' in val: # Frações como 1/3
                try:
                    num, den = val.split('/')
                    val = float(num) / float(den)
                except: pass
            elif val.isdigit():
                val = int(val)
            consensus_data[k] = val
        ast["consensus"] = consensus_data

    # Extrair regulação
    reg_match = re.search(r'regulation:\s*\[(.*?)\]', clean_code)
    if reg_match:
        ast["regulation"] = [r.strip().replace('"', '') for r in reg_match.group(1).split(',')]

    # Extrair performance
    perf_match = re.search(r'performance:\s*\{(.*?)\}', clean_code, re.DOTALL)
    if perf_match:
        perf_data = {}
        pairs = re.findall(r'(\w+):\s*([^,\n}]+)', perf_match.group(1))
        for k, v in pairs:
            val = v.strip()
            if val.isdigit():
                val = int(val)
            perf_data[k] = val
        ast["performance"] = perf_data

    # Extrair integrações
    int_match = re.search(r'integrates_with:\s*\[(.*?)\]', clean_code, re.DOTALL)
    if int_match:
        ast["integrates_with"] = [i.strip().replace('"', '') for i in int_match.group(1).split(',') if i.strip()]

    # Extrair restrições
    const_match = re.search(r'constraints:\s*\[(.*?)\]', clean_code, re.DOTALL)
    if const_match:
        ast["constraints"] = [c.strip().replace('"', '') for c in const_match.group(1).split(',') if c.strip()]

    return ast
