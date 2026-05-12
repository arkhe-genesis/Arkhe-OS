class ProtocoloArkhe:
    def verificar(self, query: str, dominio: str, contexto: str = "", metadados: dict = None) -> dict:
        return {
            "veredito": "verificado",
            "confianca": 1.0,
            "fontes": [],
            "raciocinio": "Simulado"
        }
