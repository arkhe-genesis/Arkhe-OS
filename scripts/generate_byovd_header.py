#!/usr/bin/env python3
# generate_byovd_header.py — Gera byovd_database.h a partir de lista JSON de drivers vulneráveis

import json
import hashlib
import sys

def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def generate_header(entries: list) -> str:
    header = """// byovd_database.h — BYOVD Vulnerable Driver Database
// Auto-generated from byovd_database.json — DO NOT EDIT
#ifndef BYOVD_DATABASE_H
#define BYOVD_DATABASE_H

#include <stdint.h>

#define BYOVD_FLAG_KERNEL_MEM  (1 << 0)
#define BYOVD_FLAG_FIRMWARE    (1 << 1)
#define BYOVD_FLAG_MSR         (1 << 2)
#define BYOVD_FLAG_CR          (1 << 3)
#define BYOVD_FLAG_REGISTRY    (1 << 4)

struct byovd_entry {
    uint8_t hash[32];           // SHA-256 do driver
    char name[128];             // Nome descritivo
    char vendor[64];            // Fabricante
    uint32_t flags;             // Capacidades perigosas (bitmask)
    char cve[32];               // CVE associado (se aplicável)
};

"""

    header += f"#define BYOVD_DB_SIZE {len(entries)}\n\n"
    header += "static const struct byovd_entry byovd_db[] = {\n"

    for i, entry in enumerate(entries):
        # Calcular hash do nome do driver (simulado — em produção: hash do binário real)
        driver_hash = sha256_hex(entry["filename"])
        hash_bytes = ", ".join(f"0x{driver_hash[i:i+2]}" for i in range(0, 64, 2))

        flags = 0
        if entry.get("kernel_memory_access"): flags |= 1 << 0
        if entry.get("firmware_access"): flags |= 1 << 1
        if entry.get("msr_access"): flags |= 1 << 2
        if entry.get("cr_access"): flags |= 1 << 3
        if entry.get("registry_access"): flags |= 1 << 4

        cve = entry.get("cve", "")

        header += f"""    {{
        .hash = {{{hash_bytes}}},
        .name = "{entry["name"]}",
        .vendor = "{entry["vendor"]}",
        .flags = 0x{flags:02X},
        .cve = "{cve}",
    }},
"""

    header += "};\n\n#endif // BYOVD_DATABASE_H\n"
    return header

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: generate_byovd_header.py <byovd_database.json>")
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        entries = json.load(f)

    print(generate_header(entries))
