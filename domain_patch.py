    def __init__(self, vocab_size=500, embed_dim=64, temperature=0.8, domain=None, auto_detect_domain=True, temporal_chain=None, enable_audit=True):
        # Vocabulário
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.vocab_embeddings = np.random.randn(vocab_size, embed_dim)
        self.vocab_embeddings /= np.linalg.norm(self.vocab_embeddings, axis=1, keepdims=True)
        self.vocab_decoder = {i: f"token_{i}" for i in range(vocab_size)}

        # Exorcista
        self.exorcist = FortifiedExorcist(self.vocab_decoder, embed_dim)

        # Campo Atratora
        self.field = AttractorField(
            alpha=1.5, beta=0.4, gamma=0.3, temperature=temperature
        )
        self.field.validate()
        self.attractor_engine = AttractorFieldEngine(self.field, self.vocab_embeddings)

        # Contexto (últimos tokens emitidos)
        self.context_tokens: List[TokenOmega] = []
        self.generated: List[TokenOmega] = []

        from src.arkhe.security.domain_profiles import DomainProfile, DomainProfileDetector
        self.domain = domain
        self.auto_detect_domain = auto_detect_domain
        self.profile_detector = DomainProfileDetector()
        self._update_attractor_profile()

        self.temporal_chain = temporal_chain
        self.enable_audit = enable_audit
        if enable_audit and temporal_chain:
            from src.arkhe.security.temporal_audit import TemporalAuditLogger
            self.audit_logger = TemporalAuditLogger(temporal_chain)
        else:
            self.audit_logger = None

    def _update_attractor_profile(self, prompt: Optional[str] = None):
        if self.auto_detect_domain and prompt:
            self.domain = self.profile_detector.detect(prompt)
        from src.arkhe.security.domain_profiles import DomainProfile
        profile = self.profile_detector.get_profile(self.domain or DomainProfile.DEFAULT)
        self.field.alpha = profile.alpha
        self.field.beta = profile.beta
        self.field.gamma = profile.gamma
        self.field.temperature = profile.temperature
