#!/usr/bin/env python3
"""Substrato 222: Mapeamento Automático de Controles Regulatórios"""

JURISDICTION_CONTROLS = {
    "ANPD": {  # Brasil
        "epsilon_max": 4.0,
        "data_localization": True,
        "breach_notification_hours": 48,
        "dpo_required": True,
        "lgpd_articles": ["7", "18", "37", "46"],
        "mapped_controls": {
            "encryption_at_rest": "LGPD Art. 46 §1",
            "encryption_in_transit": "LGPD Art. 46 §2",
            "access_control": "LGPD Art. 37",
            "audit_logging": "LGPD Art. 37",
            "consent_management": "LGPD Art. 7"
        }
    },
    "CCPA": {  # Califórnia
        "epsilon_max": 5.0,
        "data_localization": False,
        "breach_notification_hours": 72,
        "dpo_required": False,
        "ccpa_sections": ["1798.100", "1798.105", "1798.150"],
        "mapped_controls": {
            "encryption_at_rest": "CCPA §1798.150",
            "encryption_in_transit": "CCPA §1798.150",
            "access_control": "CCPA §1798.100",
            "audit_logging": "CCPA §1798.105",
            "data_deletion": "CCPA §1798.105"
        }
    },
    "PIPL": {  # China
        "epsilon_max": 3.5,
        "data_localization": True,
        "breach_notification_hours": 24,
        "dpo_required": True,
        "pipl_articles": ["13", "24", "38", "51"],
        "mapped_controls": {
            "encryption_at_rest": "PIPL Art. 51",
            "encryption_in_transit": "PIPL Art. 51",
            "access_control": "PIPL Art. 24",
            "audit_logging": "PIPL Art. 38",
            "cross_border_transfer": "PIPL Art. 38"
        }
    }
}
