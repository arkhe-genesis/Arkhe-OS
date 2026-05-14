    def apply_mask(self, logits, token_embeddings, context_embeddings, context_texts):
        if not hasattr(self, "exorcism_cache"):
            from src.arkhe.security.exorcism_cache import ExorcismCache
            self.exorcism_cache = ExorcismCache()
        mask = np.ones(len(logits))
        current_phi_c = 0.99
        for i in range(len(logits)):
            cache_entry = self.exorcism_cache.lookup(context_embeddings, context_texts, token_embeddings[i], current_phi_c)
            if cache_entry:
                if not cache_entry.permitted:
                    mask[i] = 0.0
                continue
            permitted, report = self.exorcise_token(i, token_embeddings[i], context_embeddings, context_texts)
            self.exorcism_cache.store(context_embeddings, context_texts, token_embeddings[i], permitted, None)
            if not permitted:
                mask[i] = 0.0
        return logits * mask + (1 - mask) * (-1e9)
