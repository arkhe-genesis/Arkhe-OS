from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import json
from contextlib import asynccontextmanager

# Cache for configuration
_config_cache = None

# Load configuration for provider routing
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "tau", "genome", "config.json")

def load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    try:
        with open(CONFIG_PATH, "r") as f:
            _config_cache = json.load(f)
            return _config_cache
    except Exception:
        return {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize config on startup
    load_config()
    yield

app = FastAPI(title="🜏 HLML LLM Middleware", lifespan=lifespan)

# Configuration for local LLM (e.g. llama.cpp)
LLM_URL = os.getenv("LLM_URL", "http://localhost:8080/completion")

class TacticRequest(BaseModel):
    goal: str
    context: str = ""

class TacticResponse(BaseModel):
    tactic: str
    confidence: float
    metadata: dict = {}

@app.post("/tactic_suggest", response_model=TacticResponse)
async def suggest_tactic(req: TacticRequest):
    """
    Bridges Lean 4 formal requests with heuristic suggestions from an LLM.
    Supports Aiden-style custom provider routing (v3.11).
    Optimized with async httpx and config caching.
    """
    config = load_config()
    primary = config.get("primary_provider", "Local")
    custom_providers = config.get("customProviders", [])

    # Resolve provider details
    provider_url = LLM_URL
    api_key = None
    model = "local"

    for cp in custom_providers:
        if cp.get("name") == primary:
            provider_url = f"{cp.get('baseUrl')}/chat/completions"
            api_key = os.getenv("BOA_API_KEY") if "${BOA_API_KEY}" in cp.get("apiKey", "") else cp.get("apiKey")
            model = cp.get("model")
            break

    prompt = f"""
    [INST] You are a Lean 4 mathematical expert.
    The current proof goal is: {req.goal}
    Additional context: {req.context}
    Suggest the most efficient and correct tactic to discharge this goal.
    Output only the tactic code. [/INST]
    """

    try:
        async with httpx.AsyncClient() as client:
            if primary == "Local":
                # This assumes a llama.cpp or compatible server is running
                response = await client.post(provider_url, json={
                    "prompt": prompt,
                    "n_predict": 64,
                    "temperature": 0.2
                }, timeout=10.0)

                if response.status_code == 200:
                    suggestion = response.json().get('content', 'simp').strip()
                    return TacticResponse(tactic=suggestion, confidence=0.85)
            else:
                # OpenAI-compatible routing
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                response = await client.post(provider_url, headers=headers, json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 64,
                    "temperature": 0.2
                }, timeout=15.0)

                if response.status_code == 200:
                    suggestion = response.json().get('choices', [{}])[0].get('message', {}).get('content', 'simp').strip()
                    return TacticResponse(tactic=suggestion, confidence=0.90, metadata={"provider": primary})

        # Fallback for mock/offline mode (avoiding silent Groq fallback)
        return TacticResponse(tactic="simp", confidence=0.3, metadata={"error": "Primary provider failed or offline"})

    except Exception as e:
        # Fallback tactic if LLM service is unreachable
        return TacticResponse(tactic="exact", confidence=0.1, metadata={"error": str(e)})

@app.get("/health")
async def health():
    return {"status": "resonant", "bridge": LLM_URL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
