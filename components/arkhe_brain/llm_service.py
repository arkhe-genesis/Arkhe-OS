import os
import time
import torch
import numpy as np
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from context_gateway import ContextCompactor

# Mock ChainClient for compilation
class ChainClient:
    def __init__(self, url):
        self.url = url
    def get_network_status(self):
        class Status:
            omega = 0.92
            active_validators = 42
            recent_anomalies = ["Minor BGP jitter on node 7", "ZK proof delay on node 12"]
            zk_proof_time_increase = "15%"
            transaction_flow = "High volume of zkERC transfers detected in the last hour."
        return Status()

def publish_to_nostr(summary):
    print(f"Published to Nostr: {summary}")

def save_to_dashboard(report):
    print(f"Saved to Dashboard: {report}")

def trigger_sentinel_alert(action):
    print(f"Sentinel Alert Triggered: {action}")

def parse_response(content):
    import json
    try:
        # Strip markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        return json.loads(content)
    except:
        return {
            "summary": "Failed to parse LLM response.",
            "risk_assessment": "UNKNOWN",
            "recommended_action": "Manual review required."
        }

# Inicialização
llm = ChatOpenAI(model="gpt-4o", temperature=0.7) if os.getenv("OPENAI_API_KEY") else None
chain_client = ChainClient("https://rpc.arkhe.network")
analysis_history = []
compactor = ContextCompactor(embed_dim=64)

def _get_deterministic_embedding(text, dim):
    """
    Returns a deterministic mock embedding for simulation.
    In production, this would be the actual embedding from the model.
    """
    import hashlib
    seed = int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)
    torch.manual_seed(seed)
    return torch.randn(1, 1, dim)

# Prompt de Análise
analysis_prompt = PromptTemplate.from_template(
    """
    You are the Arkhe Brain, an autonomous AI monitoring a post-quantum blockchain.
    
    Coherent History Projection (Compressed Context):
    {history_summary}

    Current Network Status:
    - Global Coherence (Ω'): {omega}
    - Active Validators: {validators}
    - Recent Anomalies: {anomalies}
    
    Transaction Context:
    - Transaction Flow: {transaction_flow}
    - ZK Proof Validation: Time increased by {zk_proof_time_increase}.
    
    Task: Generate a concise status report for the operators and suggest one action to optimize network health.
    Output format: JSON with keys 'summary', 'risk_assessment', 'recommended_action'.
    """
)

# Prompt de Análise de Storage
storage_analysis_prompt = PromptTemplate.from_template(
    """
    You are the Arkhe Brain, an autonomous AI monitoring the TimeChain storage layer.
    
    Recent storage metrics:
    - Average query latency: {avg_latency} ms
    - Storage node distances: {distances}
    - Batch sizes used: {batch_sizes}
    - Reputation scores: {reputations}
    
    Analyze the storage system's health and suggest improvements.
    Output format: JSON with keys 'summary', 'efficiency_score', 'recommended_action'.
    """
)

def run_storage_analysis_cycle():
    if not llm:
        print("OPENAI_API_KEY not set. Skipping storage analysis cycle.")
        return
        
    # Mock storage metrics
    metrics = {
        "avg_latency": 12.5,
        "distances": "[10km, 50km, 120km]",
        "batch_sizes": "[100, 250, 500]",
        "reputations": "[0.99, 0.95, 0.88]"
    }
    
    chain = storage_analysis_prompt | llm
    response = chain.invoke(metrics)
    
    report = parse_response(response.content)
    
    print(f"Storage Analysis Report: {report}")
    return report

def run_analysis_cycle():
    global analysis_history
    if not llm:
        print("OPENAI_API_KEY not set. Skipping analysis cycle.")
        return
        
    # 1. Coletar Dados On-Chain
    status = chain_client.get_network_status()
    
    # 2. Gerenciar Context Gateway (Compaction)
    history_summary = "No previous context."
    if len(analysis_history) >= 5:
        # Simulate background compaction
        embeddings = [_get_deterministic_embedding(str(h), 64) for h in analysis_history]
        history_tensor = torch.cat(embeddings, dim=1) # (1, seq, 64)
        compressed_state = compactor.compact(history_tensor)
        history_summary = f"Arkhe-H_eta Projection: {compressed_state.detach().numpy().tolist()}"
        print(f"Context Gateway: History compacted (len={len(analysis_history)})")

        # Clear history after compaction to simulate window slide/reset
        # In a real proxy, this would be an O(1) state update.
        analysis_history = analysis_history[-2:]

    # 3. Alimentar LLM
    chain = analysis_prompt | llm
    response = chain.invoke({
        "omega": status.omega,
        "validators": status.active_validators,
        "anomalies": status.recent_anomalies,
        "transaction_flow": status.transaction_flow,
        "zk_proof_time_increase": status.zk_proof_time_increase,
        "history_summary": history_summary
    })
    
    # 4. Processar Output
    report = parse_response(response.content)
    
    # 5. Adicionar ao histórico para próxima compactação
    analysis_history.append(report)

    # 6. Publicar Relatório (Nostr + Dashboard)
    publish_to_nostr(report['summary'])
    save_to_dashboard(report)
    
    # 7. Se ação recomendada for crítica, alertar via Sentinel
    if report['risk_assessment'] == 'HIGH':
        trigger_sentinel_alert(report['recommended_action'])

    return report

# Rodar a cada hora
if __name__ == "__main__":
    import schedule
    schedule.every(1).hours.do(run_analysis_cycle)
    schedule.every(2).hours.do(run_storage_analysis_cycle)
    
    print("Arkhe Brain initialized. Running schedule...")
    while True:
        schedule.run_pending()
        time.sleep(1)
