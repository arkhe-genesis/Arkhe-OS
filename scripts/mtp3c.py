#!/usr/bin/env python3
"""
MTP 3.0 COMPILER (mtp3c)
Uso: python mtp3c.py <arquivo.arkhe> [-o <saída.mtp3>]

Converte um script ArkheScript que descreve um Substrato em um pacote MTP 3.0.
"""

import json, hashlib, struct, zipfile, os, sys, argparse
from datetime import datetime

MTP3_MAGIC = b'\x89MTP3\r\n\x1a\n'
MTP3_VERSION = 1

class MTP3Compiler:
    def __init__(self, arkhe_path):
        with open(arkhe_path, 'r') as f:
            self.script = f.read()
        self.manifest = {}
        self.services = []
        self.alarms = []
        self.harmonics = []
        self.coupling = {}
        self.initial_state = {}
        self.substrate_id = 0
        self.substrate_name = ""

    def parse(self):
        """Extrai metadados do ArkheScript."""
        lines = self.script.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('let substrate_id'):
                try:
                    self.substrate_id = int(line.split('=')[1].strip().rstrip(' ~'))
                except: pass
            elif line.startswith('let substrate_name'):
                self.substrate_name = line.split('=')[1].strip().strip('"~ ')
            elif line.startswith('let harmonics'):
                try:
                    raw = line.split('=')[1].strip().strip('[]~ ')
                    self.harmonics = [float(x) for x in raw.split(',') if x]
                except: pass
            elif line.startswith('let J_coupling'):
                try:
                    self.coupling['J'] = float(line.split('=')[1].strip().rstrip(' ~'))
                except: pass
            elif line.startswith('let h_field'):
                try:
                    self.coupling['h'] = float(line.split('=')[1].strip().rstrip(' ~'))
                except: pass
            elif line.startswith('let T_max'):
                try:
                    self.coupling['T_max'] = float(line.split('=')[1].strip().rstrip(' ~'))
                except: pass
            elif line.startswith('let Phi_min'):
                try:
                    self.coupling['Phi_min'] = float(line.split('=')[1].strip().rstrip(' ~'))
                except: pass
            elif 'service' in line.lower():
                self.services.append({"name": line.strip(), "type": "quantum_port"})
            elif 'alarm' in line.lower():
                self.alarms.append({"name": line.strip(), "condition": "manual"})

        if not self.substrate_name:
            self.substrate_name = f"Substrate_{self.substrate_id}"

    def build_manifest(self):
        self.manifest = {
            "mtp_version": "3.0",
            "module_type": "invariant_package",
            "substrate_id": self.substrate_id,
            "substrate_name": self.substrate_name,
            "coherence_class": "high",
            "harmonics_count": len(self.harmonics),
            "services": self.services,
            "alarms": self.alarms,
            "coupling": self.coupling
        }

    def compile(self, output_path):
        self.parse()
        self.build_manifest()

        # Arquivos internos do ZIP
        manifest_json = json.dumps(self.manifest, indent=2)
        state_rom = hashlib.sha3_256(self.script.encode()).digest()
        script_bytes = self.script.encode()
        coupling_json = json.dumps(self.coupling, indent=2)
        services_json = json.dumps(self.services, indent=2)
        signature = hashlib.sha3_256(manifest_json.encode() + script_bytes + state_rom).hexdigest()

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('manifest.json', manifest_json)
            zf.writestr('substrate.arkhe', script_bytes)
            zf.writestr('state.rom', state_rom)
            zf.writestr('coupling.matrix', coupling_json)
            zf.writestr('services.json', services_json)
            zf.writestr('signature.sha3', signature)

        print(f"✅ Pacote MTP 3.0 gerado: {output_path}")
        print(f"   Substrato: {self.substrate_name} (ID {self.substrate_id})")
        print(f"   Assinatura: {signature[:16]}...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compilador MTP 3.0")
    parser.add_argument("input", help="Arquivo ArkheScript (.arkhe)")
    parser.add_argument("-o", "--output", help="Arquivo de saída (.mtp3)", default=None)
    args = parser.parse_args()
    out = args.output or os.path.splitext(args.input)[0] + ".mtp3"
    compiler = MTP3Compiler(args.input)
    compiler.compile(out)
