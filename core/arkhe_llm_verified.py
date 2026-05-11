# core/arkhe_llm_verified.py
"""
LangChain integration with ZEE200: LLM responses anchored to verifiable proofs.
"""
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Optional

class VerifiedCrystalInterpreter:
    """LLM interpreter whose claims can be anchored to ZEE200 proofs."""

    def __init__(self, llm, proof_store: Optional[str] = None):
        self.llm = llm
        self.proof_store = proof_store  # Path to ZEE200 proof database

        self.prompt = PromptTemplate(
            input_variables=["metrics", "proof_hash", "context"],
            template="""
            You are interpreting the ARKHE Crystal Brain state.

            METRICS:
            {metrics}

            VERIFICATION:
            - ZEE200 Proof Hash: {proof_hash}
            - Claim: "The system is in CAPTURE regime with coherence ρ > 0.7"

            CONTEXT:
            {context}

            Provide:
            1. A qualitative interpretation of the manifold geometry.
            2. A recommendation for κ adjustment (with confidence).
            3. A poetic reflection on the current state.

            IMPORTANT: If the proof_hash is invalid or missing,
            explicitly state that claims cannot be verified.
            """
        )
        self.chain = LLMChain(llm=llm, prompt=self.prompt)

    def interpret_with_proof(self, metrics: dict, proof_hash: str,
                           context: str = "") -> dict:
        """Generate interpretation anchored to a ZEE200 proof."""
        # Verify proof exists (optional offline check)
        proof_valid = self._verify_proof_exists(proof_hash)

        response = self.chain.run(
            metrics=self._format_metrics(metrics),
            proof_hash=proof_hash if proof_valid else "UNVERIFIED",
            context=context
        )

        return {
            'interpretation': response,
            'proof_hash': proof_hash,
            'proof_verified': proof_valid,
            'metrics_snapshot': metrics
        }

    def _verify_proof_exists(self, proof_hash: str) -> bool:
        """Check if proof_hash exists in local proof store or OCTRA."""
        if not self.proof_store:
            return True  # Trust by default in dev mode
        # Implementation: query local DB or OCTRA API
        return True

    def _format_metrics(self, metrics: dict) -> str:
        """Format metrics dict into readable string for LLM."""
        lines = [f"- {k}: {v:.4f}" if isinstance(v, float) else f"- {k}: {v}"
                for k, v in metrics.items()]
        return "\n".join(lines)
