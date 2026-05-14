import sys
import os
from . import compat
from .audit_hooks import auditor

def main():
    if len(sys.argv) < 2:
        print("Uso: arkhe-stdlib [enable|disable|status|audit]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "enable":
        print("Para ativar, execute:")
        print("export ARKHE_STDLIB_ENABLED=1")
    elif command == "disable":
        print("Para desativar, execute:")
        print("unset ARKHE_STDLIB_ENABLED")
    elif command == "status":
        print(compat.status())
    elif command == "audit":
        print(f"Auditoria - Bloqueios Totais: {auditor.blocked_calls}")
    else:
        print(f"Comando desconhecido: {command}")
        print("Comandos disponíveis: enable, disable, status, audit")
        sys.exit(1)

if __name__ == "__main__":
    main()
