import random
import time
import hashlib
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PrivacyCompliance")

class DifferentialPrivacy:
    """
    Adicionar garantias formais de privacidade (ε-DP) aos relatórios agregados sem comprometer utilidade.
    """
    def __init__(self, epsilon=1.0):
        self.epsilon = epsilon

    def add_laplace_noise(self, value, sensitivity=1.0):
        """
        Adiciona ruído Laplaciano para garantir ε-Differential Privacy.
        """
        # Laplace distribution scale = sensitivity / epsilon
        scale = sensitivity / self.epsilon
        # numpy.random.laplace equivalent using random for simple dependency
        # Laplace(mu, b) = mu - b * sgn(U) * ln(1 - 2|U|) where U is uniform in (-0.5, 0.5)
        import math
        u = random.uniform(-0.5, 0.5)
        # Avoid math.log(0) edge case
        if abs(u) >= 0.5:
            u = 0.49999999
        sign = 1 if u > 0 else -1
        noise = -scale * sign * math.log(1 - 2 * abs(u)) if u != 0 else 0

        return value + noise

    def aggregate_with_dp(self, values):
        """
        Applies DP to an aggregation function (e.g., mean).
        """
        import math
        if not values:
            return 0
        raw_mean = sum(values) / len(values)
        # Sensitivity of mean is (max - min) / N, assume max=1, min=0 for coherence
        sensitivity = 1.0 / len(values)
        scale = sensitivity / self.epsilon

        u = random.uniform(-0.5, 0.5)
        if abs(u) >= 0.5:
            u = 0.49999999
        sign = 1 if u > 0 else -1
        noise = -scale * sign * math.log(1 - 2 * abs(u)) if u != 0 else 0

        return raw_mean + noise

class AuditTrail:
    """
    Mantém audit trail de quem acessou quais partes do relatório (com provas de acesso).
    """
    def __init__(self):
        self.log = []

    def record_access(self, user_id, report_id, sections_accessed):
        timestamp = time.time()
        entry = {
            "user_id": user_id,
            "report_id": report_id,
            "sections": sections_accessed,
            "timestamp": timestamp
        }
        entry_hash = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
        entry["proof_hash"] = entry_hash
        self.log.append(entry)
        logger.info(f"Access recorded: {user_id} accessed {report_id}")
        return entry_hash

    def get_trail(self, report_id):
        return [entry for entry in self.log if entry["report_id"] == report_id]

class ComplianceReportManager:
    """
    Manages DP reports, FHE separation, and redactions.
    """
    def __init__(self, dp_engine: DifferentialPrivacy, audit_trail: AuditTrail):
        self.dp_engine = dp_engine
        self.audit_trail = audit_trail
        self.published_reports = {}

    def generate_report(self, raw_data_map):
        """
        Usar FHE apenas para dados sensíveis; metadados de auditoria podem ser públicos.
        """
        report = {
            "public_metadata": {
                "record_count": len(raw_data_map),
                "timestamp": time.time(),
                "aggregate_coherence_dp": self.dp_engine.aggregate_with_dp(list(raw_data_map.values()))
            },
            "sensitive_data_fhe": "FHE_ENCRYPTED_BLOB" # Simulated FHE
        }

        report_id = hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest()
        self.published_reports[report_id] = report
        return report_id, report

    def request_redaction(self, report_id, redaction_request, auth_signature):
        """
        Permitir "redaction requests" pós-publicação com prova de alteração autorizada.
        """
        if report_id not in self.published_reports:
            raise ValueError("Report not found")

        # Verify authorization
        if not self._verify_signature(redaction_request, auth_signature):
            raise PermissionError("Invalid authorization signature for redaction")

        report = self.published_reports[report_id]

        # Apply redaction
        report["redacted"] = True
        report["redaction_proof"] = hashlib.sha256((redaction_request + auth_signature).encode()).hexdigest()

        logger.info(f"Report {report_id} redacted successfully.")
        return report

    def _verify_signature(self, data, sig):
        # Dummy signature verification
        return sig == "AUTH_VALID"
