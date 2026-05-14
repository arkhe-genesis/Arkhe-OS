class HyperLLMNode:
    def __init__(self, node_id, temporal_chain):
        self.node_id = node_id
        self.temporal = temporal_chain

    async def forward(self, input_ids, trace_id):
        # executa camadas da partição
        # ao final, ancorar no TemporalChain
        await self.temporal.anchor_event("hyper_llm_forward", {
            "trace_id": trace_id, "node": self.node_id
        })
        logits = [0.0] * len(input_ids) # mock
        return logits
