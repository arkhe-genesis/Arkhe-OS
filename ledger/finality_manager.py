# Arquivo: ledger/finality_manager.py
class FinalityManager:
    def __init__(self):
        self.batch_settlement_interval_s = 86400  # 24 h
        self.k_confirmation_threshold = 202
        self.cross_zone_rtt_s = 5160  # 86 min Terra<->Europa

    def estimate_finality_time(self, vc_type: str) -> float:
        if vc_type in ["resource_transfer", "operational_log"]:
            # Batch settlement: finalidade em 24 h
            return self.batch_settlement_interval_s
        elif vc_type in ["crewed_mission", "scientific_discovery"]:
            # k-confirmation: finalidade em ~12 dias
            return self.k_confirmation_threshold * self.cross_zone_rtt_s
        else:
            # Default conservador
            return self.k_confirmation_threshold * self.cross_zone_rtt_s
