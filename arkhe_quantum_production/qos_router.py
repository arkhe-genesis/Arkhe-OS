class PhiCQosRouter:
    def route(self, packet):
        return {"routed": True, "phi_c": 0.99}
