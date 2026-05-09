"""
ARKHE OS — Cathedral Design System (Substrato 292)
Implementação da paleta de cores e princípios visuais da Catedral.
"""

from typing import Dict, Tuple

class CathedralDesignSystem:
    """
    Design System canônico para a interface do ARKHE OS,
    mapeando coerência Φ_C para cores, conforme o Substrato 292.
    """

    # Espectro Φ_C (vermelho → violeta)
    PHI_SPECTRUM: Dict[str, Dict[str, str]] = {
        "critical":   {"hex": "#FF1A1A", "range": [0.00, 0.20], "desc": "Vermelho intenso: ação imediata necessária"},
        "high_risk":  {"hex": "#FF8C00", "range": [0.20, 0.40], "desc": "Laranja: alto risco"},
        "moderate":   {"hex": "#FFD700", "range": [0.40, 0.60], "desc": "Amarelo: atenção recomendada"},
        "acceptable": {"hex": "#ADFF2F", "range": [0.60, 0.75], "desc": "Amarelo-esverdeado: melhoria desejável"},
        "good":       {"hex": "#32CD32", "range": [0.75, 0.85], "desc": "Verde: dentro do esperado"},
        "very_good":  {"hex": "#1E90FF", "range": [0.85, 0.95], "desc": "Azul: alta coerência"},
        "excellent":  {"hex": "#8A2BE2", "range": [0.95, 1.00], "desc": "Violeta: coerência máxima"}
    }

    @classmethod
    def get_color_for_phi(cls, phi: float) -> str:
        """Retorna o código HEX para um determinado valor de Φ_C (0.0 a 1.0)."""
        # Clamp value to 0-1
        phi = max(0.0, min(1.0, phi))

        for level, data in cls.PHI_SPECTRUM.items():
            r = data["range"]
            # Inclui o limite superior se for 1.0
            if r[0] <= phi < r[1] or (phi == 1.0 and r[1] == 1.0):
                return data["hex"]

        return cls.PHI_SPECTRUM["critical"]["hex"] # Fallback

    @classmethod
    def hex_to_ansi(cls, hex_color: str) -> str:
        """Converte uma string HEX (#RRGGBB) para escape code ANSI de 24 bits."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f"\033[38;2;{r};{g};{b}m"
        return "\033[0m"

    @classmethod
    def get_ansi_for_phi(cls, phi: float) -> str:
        """Retorna a cor ANSI para o terminal baseada no Φ_C."""
        hex_color = cls.get_color_for_phi(phi)
        return cls.hex_to_ansi(hex_color)

    @staticmethod
    def get_status_icon(phi: float) -> str:
        """Retorna o ícone de status (✅, ⚠️, ❌) para o Φ_C."""
        if phi < 0.40: return "❌"
        elif phi < 0.75: return "⚠️ "
        else: return "✅"
