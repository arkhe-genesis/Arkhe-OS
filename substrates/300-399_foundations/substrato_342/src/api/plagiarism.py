# src/api/plagiarism.py
from fastapi import APIRouter, HTTPException
from plagiarism.code_plagiarism_engine import CodePlagiarismEngine
from hashtree import compute_merkle_root, generate_proof
import hashlib, json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

router = APIRouter()
engine = CodePlagiarismEngine()

@router.post("/api/v1/plagiarism/check")
async def check_plagiarism_with_proof(
    code_a: str,
    code_b: str,
    language: str = "solidity",
    include_merkle_proof: bool = True
):
    # Executar detecção de plágio
    result = engine.detect_plagiarism(code_a, code_b, language)

    if include_merkle_proof and result.stage_reached >= 2:
        # Gerar prova Merkle da comparação
        leaves = [
            hashlib.sha3_256(code_a.encode()).digest(),
            hashlib.sha3_256(code_b.encode()).digest(),
            hashlib.sha3_256(json.dumps({
                "jaccard": result.jaccard_similarity,
                "ast": result.ast_similarity,
                "graph": result.graph_similarity,
                "timestamp": result.timestamp,
                "version": "342.1.0"
            }).encode()).digest(),
        ]
        merkle_data = compute_merkle_root(leaves)

        # Prova para verificar o veredicto (leaf 2)
        proof = generate_proof(merkle_data["proof_map"], 2)

        result.merkle_proof = {
            "root": merkle_data["root"].hex(),
            "proof": [p.hex() for p in proof],
            "leaf_index": 2,
        }

    return result
