# vro_evaluator.py
import azure.functions as func
import logging
import json
import os
import numpy as np
from azure.cosmos.aio import CosmosClient

# Note: Weaviate client omitted for brevity in MVP script,
# can be added as per requirement.

app = func.FunctionApp()

@app.service_bus_topic_trigger(
    arg_name="msg",
    topic_name="task-completed",
    subscription_name="vro-evaluator",
    connection="ServiceBusConnection"
)
async def evaluate_task(msg: func.ServiceBusMessage):
    logging.info(f"VRO: Avaliando tarefa {msg.message_id}")

    try:
        body = json.loads(msg.get_body().decode())
        task_intent_embedding = body.get('intent_embedding')
        result_embedding = body.get('result_embedding')
        agent_did = body.get('agent_did')

        if not task_intent_embedding or not result_embedding:
            logging.warning("Embeddings missing in task completion message.")
            return

        # 1. Calcular Coerência Semântica
        similarity = cosine_similarity(task_intent_embedding, result_embedding)
        logging.info(f"Similaridade calculada: {similarity}")

        # 2. Mock Novelty calculation
        novelty = 0.92

        # 3. Determinar novo score de reputação
        current_vector = await get_reputation_vector(agent_did)
        new_vector = update_vector(current_vector, similarity, novelty)

        # 4. Armazenar o vetor atualizado no Cosmos DB
        await store_reputation_vector(agent_did, new_vector)

        logging.info(f"Vetor de reputação atualizado para {agent_did}: {new_vector}")

    except Exception as e:
        logging.error(f"Erro no VROEvaluator: {e}")

def cosine_similarity(a, b):
    a = np.array(a); b = np.array(b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0
    return np.dot(a, b) / (norm_a * norm_b)

async def get_reputation_vector(did):
    # Mock lookup
    return {"semantic": 800, "punctuality": 750, "economic": 900, "originality": 700}

async def store_reputation_vector(did, vector):
    connection_str = os.getenv("COSMOS_CONNECTION_STRING")
    if not connection_str:
        logging.warning("COSMOS_CONNECTION_STRING not set.")
        return

    database_name = "ArkheMemory"
    container_name = "Reputation"

    async with CosmosClient.from_connection_string(connection_str) as client:
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)

        # Add id and partition key
        vector['id'] = did
        vector['did'] = did
        vector['type'] = 'reputation'

        await container.upsert_item(vector)
        logging.info(f"Successfully saved reputation {vector} for DID {did} to Cosmos DB")

def update_vector(current, similarity, novelty):
    new_vec = current.copy()
    if similarity >= 0.85:
        new_vec['semantic'] = min(1000, new_vec['semantic'] + 10)
    elif similarity < 0.65:
        new_vec['semantic'] = max(0, new_vec['semantic'] - 50)

    new_vec['originality'] = min(1000, new_vec['originality'] + int((novelty - 0.8) * 200))
    return new_vec
