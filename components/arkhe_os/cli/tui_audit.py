"""
ARKHE OS — Interactive Audit TUI (Substrato 292)
Implementação de TUI em Python para o modo interativo de auditoria de coerência,
usando a paleta de cores canônica de Φ_C (vermelho → violeta).
"""
import sys
import argparse
from typing import Dict, List
import json
from arkhe_os.ui.cathedral.cathedral_design_system import CathedralDesignSystem

def render_bar(phi: float, width: int = 20) -> str:
    filled = int(phi * width)
    empty = width - filled
    color = CathedralDesignSystem.get_ansi_for_phi(phi)
    # Using block chars for UI consistency: ██ / ░░
    return f"{color}{'█' * filled}{'░' * empty}\033[0m"

def draw_tui(repository: str, npub: str, global_phi: float, files_data: List[Dict]):
    print("┌─────────────────────────────────────────────────────────┐")
    print(f"│  ARKHE OS — Interactive Audit                    {npub: >8} │")
    print("├─────────────────────────────────────────────────────────┤")
    print(f"│  Repository: {repository:<16} Φ_C Global: {global_phi:.2f}       │")
    print("│                                                         │")
    print("│  Files                          Coherence               │")
    print("│  ─────────────────────────────────────────────────────  │")

    for item in files_data:
        path = item.get("path", "")
        phi = item.get("phi", 0.0)
        bar = render_bar(phi)
        icon = CathedralDesignSystem.get_status_icon(phi)
        # Formatar a linha perfeitamente espaçada
        # Usamos :<20 para o caminho do arquivo para garantir o alinhamento
        print(f"│  {bar}  {path:<20} {phi:.2f} {icon}     │")

    print("│                                                         │")
    print("│  [↑↓ Navigate] [Enter Details] [R Refresh] [Q Quit]     │")
    print("└─────────────────────────────────────────────────────────┘")

def main():
    parser = argparse.ArgumentParser(description="ARKHE OS Interactive Audit TUI (Cathedral UI/UX)")
    parser.add_argument("--repo", type=str, default="my-project", help="Nome do repositório")
    parser.add_argument("--npub", type=str, default="npub1abc", help="Nostr Pubkey do usuário")
    args = parser.parse_args()

    # Mock data para visualização
    mock_files = [
        {"path": "core/parser.py", "phi": 0.94},
        {"path": "api/handler.py", "phi": 0.72},
        {"path": "utils/validator.py", "phi": 0.88},
        {"path": "legacy/deprecated.py", "phi": 0.31},
    ]

    global_phi = sum(item["phi"] for item in mock_files) / len(mock_files)

    draw_tui(args.repo, args.npub, global_phi, mock_files)

if __name__ == "__main__":
    main()
