from typing import Dict, Any

class LFIRMemoryIntegration:
    """Integration of LFIR Graph Engine Core with the Memory Architecture."""
    def __init__(self, retrieval_engine):
        self.retrieval_engine = retrieval_engine

    def query_memory(self, lfir_query: Dict[str, Any]) -> Any:
        return self.retrieval_engine.retrieve(lfir_query)
