from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from arkhe_os.core.scaffold import ScaffoldState
from arkhe_os.core.sato_tokenizer import SATOTokenizer

router = APIRouter(prefix="/v1/sato", tags=["SATO"])

def get_scaffold_state() -> ScaffoldState:
    """Dependência injetada para o estado do Scaffold."""
    raise NotImplementedError("Dependência deve ser sobrescrita pelo app principal.")

@router.post("/tokenize")
async def tokenize_mesh(mesh_data: Dict[str, Any], scaffold: ScaffoldState = Depends(get_scaffold_state)):
    """
    Tokeniza uma malha 3D usando o algoritmo SATO (Strips as Tokens).
    """
    try:
        tokenizer = SATOTokenizer(mesh_data)
        tokens = tokenizer.serialize()

        # Atualizar estado do Scaffold com a nova geometria tokenizada
        scaffold.sato_tokenizer = tokenizer
        scaffold.geometric_tokens = tokens

        return {
            "status": "success",
            "token_count": len(tokens),
            "strip_count": tokenizer.count_strips(),
            "tokens_preview": tokens[:10] if len(tokens) > 10 else tokens
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro na tokenização SATO: {str(e)}")

@router.get("/tokens")
async def get_current_tokens(scaffold: ScaffoldState = Depends(get_scaffold_state)):
    """Retorna os tokens geométricos atuais do Scaffold Ξ."""
    if not scaffold.geometric_tokens:
        return {"tokens": [], "message": "Nenhuma geometria tokenizada no Scaffold."}
    return {"tokens": scaffold.geometric_tokens}
