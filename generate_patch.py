    def generate_token(self, prompt: Optional[str] = None) -> TokenOmega:
        if self.auto_detect_domain and prompt and not self.domain:
            self._update_attractor_profile(prompt)
