        if getattr(self, 'audit_logger', None):
            import asyncio
            exorcism_report = {
                "blocked": False, # Mock
                "reason": None,
                "severity": 0.0,
            }

            attractor_metrics = {
                "coherence": token.coherence,
                "surprise": token.surprise,
                "resonance": token.resonance,
                "potential": token.potential,
            }

            try:
                asyncio.get_running_loop()
                asyncio.create_task(
                    self.audit_logger.log_token(
                        token_id=token.id,
                        token_text=self.vocab_decoder.get(token.id, f"<{token.id}>"),
                        position=token.position,
                        exorcism_report=exorcism_report,
                        attractor_metrics=attractor_metrics,
                        final_probability=token.probability,
                        context_embeddings=[t.embedding for t in self.context_tokens[-5:]],
                        domain_profile=self.domain.value if hasattr(self, 'domain') and self.domain else None,
                    )
                )
            except RuntimeError:
                pass
