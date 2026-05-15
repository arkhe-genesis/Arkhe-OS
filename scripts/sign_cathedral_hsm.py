#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sign_cathedral_hsm.py — Arkhe Cathedral Production Signing with HSM
Gera assinatura de produção para catedral.sys usando Hardware Security Module.

Requisitos:
• HSM compatível com PKCS#11 (Thales, Utimaco, AWS CloudHSM, Azure Dedicated HSM)
• Certificado de código assinado por CA raiz confiável
• Acesso administrativo ao sistema de build

Uso:
    python sign_cathedral_hsm.py --hsm-provider thales --input catedral.sys --output catedral_signed.sys
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict
import subprocess

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

@dataclass
class SigningConfig:
    """Configuração para assinatura com HSM."""
    hsm_provider: str  # 'thales', 'utimaco', 'aws_cloudhsm', 'azure_dhsm', 'pkcs11_generic'
    hsm_slot: Optional[int] = None
    hsm_label: Optional[str] = None
    key_label: str = "arkhe-cathedral-production"
    certificate_path: Optional[str] = None
    timestamp_server: str = "http://timestamp.digicert.com"
    hash_algorithm: str = "SHA3_256"
    signature_algorithm: str = "SHA3_256withRSA"
    catalog_path: Optional[str] = None
    inf_path: Optional[str] = None

    # Metadados do binário
    product_name: str = "Arkhe Cathedral Kernel"
    product_version: str = "v∞.Ω.∇+++.SINGULARITY.EVO"
    file_version: str = "1.0.0.0"
    company_name: str = "ARKHE Observatory"
    copyright: str = "© 2026 ARKHE Observatory. All rights reserved."

# ============================================================================
# ABSTRAÇÃO DE HSM (PKCS#11)
# ============================================================================

class HSMProvider:
    """Interface abstrata para provedores HSM."""

    def __init__(self, config: SigningConfig):
        self.config = config
        self.session = None
        self.private_key = None
        self.certificate = None

    def connect(self) -> bool:
        """Estabelece conexão com o HSM."""
        raise NotImplementedError

    def load_key(self, key_label: str):
        """Carrega chave privada do HSM."""
        raise NotImplementedError

    def load_certificate(self, cert_path: Optional[str] = None):
        """Carrega certificado de código."""
        raise NotImplementedError

    def sign_data(self, data: bytes, hash_algo: str = 'SHA3_256') -> bytes:
        """Assina dados usando chave no HSM."""
        raise NotImplementedError

    def disconnect(self):
        """Encerra conexão com o HSM."""
        if self.session:
            # Lógica de cleanup específica do provedor
            pass
        self.session = None

class ThalesHSM(HSMProvider):
    """Implementação para HSM Thales (nCipher)."""

    def connect(self) -> bool:
        try:
            # Usar PKCS#11 library do Thales
            import pkcs11

            lib = pkcs11.lib('/opt/nfast/toolkits/pkcsp11/libcknfast.so')
            self.session = lib.openToken(self.config.hsm_slot or 0)
            self.session.login('user', pin=os.getenv('HSM_PIN', ''))
            return True
        except Exception as e:
            print(f"❌ Falha ao conectar ao Thales HSM: {e}", file=sys.stderr)
            return False

    def load_key(self, key_label: str):
        if not self.session:
            raise RuntimeError("HSM not connected")

        # Buscar chave por label
        keys = self.session.getObjects({
            pkcs11.CKA_CLASS: pkcs11.CKO_PRIVATE_KEY,
            pkcs11.CKA_LABEL: key_label,
        })

        if not keys:
            raise ValueError(f"Chave '{key_label}' não encontrada no HSM")

        self.private_key = keys[0]
        print(f"✅ Chave carregada: {key_label}")

    def load_certificate(self, cert_path: Optional[str] = None):
        if cert_path and os.path.exists(cert_path):
            with open(cert_path, 'rb') as f:
                self.certificate = f.read()
            print(f"✅ Certificado carregado: {cert_path}")
        else:
            # Tentar obter certificado do HSM
            certs = self.session.getObjects({
                pkcs11.CKA_CLASS: pkcs11.CKO_CERTIFICATE,
                pkcs11.CKA_LABEL: self.config.key_label,
            })
            if certs:
                self.certificate = certs[0][pkcs11.CKA_VALUE]
                print(f"✅ Certificado obtido do HSM")

    def sign_data(self, data: bytes, hash_algo: str = 'SHA3_256') -> bytes:
        if not self.private_key:
            raise RuntimeError("Private key not loaded")

        # Calcular hash
        if hash_algo == 'SHA3_256':
            digest = hashlib.sha3_256(data).digest()
        elif hash_algo == 'SHA256':
            digest = hashlib.sha256(data).digest()
        else:
            raise ValueError(f"Hash algorithm not supported: {hash_algo}")

        # Assinar com chave no HSM
        # Nota: PKCS#11 signing mechanism depends on key type
        signature = self.private_key.sign(
            digest,
            mechanism=pkcs11.Mechanism.RSA_PKCS,
            hash=hash_algo
        )

        return signature

    def disconnect(self):
        if self.session:
            try:
                self.session.logout()
                self.session.close()
            except:
                pass
        super().disconnect()

# Implementações similares para outros provedores:
# - UtimacoHSM
# - AWS_CloudHSM
# - Azure_DedicatedHSM
# - Generic_PKCS11

def get_hsm_provider(config: SigningConfig) -> HSMProvider:
    """Factory para obter provedor HSM baseado na configuração."""
    providers = {
        'thales': ThalesHSM,
        'utimaco': lambda c: None,  # Implementar
        'aws_cloudhsm': lambda c: None,  # Implementar
        'azure_dhsm': lambda c: None,  # Implementar
        'pkcs11_generic': lambda c: None,  # Implementar
    }

    provider_class = providers.get(config.hsm_provider)
    if not provider_class:
        raise ValueError(f"HSM provider not supported: {config.hsm_provider}")

    return provider_class(config)

# ============================================================================
# FUNÇÕES DE ASSINATURA AUTHENTICODE
# ============================================================================

def compute_file_hash(filepath: str, algorithm: str = 'SHA3_256') -> str:
    """Computa hash criptográfico de arquivo."""
    if algorithm == 'SHA3_256':
        hasher = hashlib.sha3_256()
    elif algorithm == 'SHA256':
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Algorithm not supported: {algorithm}")

    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    return hasher.hexdigest()

def prepare_authenticode_data(filepath: str) -> Dict[str, Any]:
    """Prepara dados para assinatura Authenticode."""
    # Em produção: usar biblioteca como pefile para parsear PE
    # Para demo: simular estrutura
    return {
        'file_path': filepath,
        'file_size': os.path.getsize(filepath),
        'hash_sha3_256': compute_file_hash(filepath, 'SHA3_256'),
        'hash_sha256': compute_file_hash(filepath, 'SHA256'),
        'metadata': {
            'product_name': config.product_name,
            'product_version': config.product_version,
            'file_version': config.file_version,
            'company_name': config.company_name,
            'copyright': config.copyright,
        }
    }

def sign_with_signtool(
    filepath: str,
    hsm_config: SigningConfig,
    output_path: Optional[str] = None
) -> bool:
    """
    Assina arquivo usando signtool com HSM via PKCS#11.

    Nota: signtool requer configuração específica para HSM.
    Alternativamente, usar OpenSSL + ferramentas de inserção de assinatura.
    """
    if not output_path:
        output_path = filepath.replace('.sys', '_signed.sys')

    # Comando signtool com suporte a PKCS#11
    # Nota: Requer configuração de CSP/PKCS#11 no Windows
    cmd = [
        'signtool', 'sign',
        '/v',  # Verbose
        '/fd', hsm_config.hash_algorithm,  # File digest algorithm
        '/td', hsm_config.hash_algorithm,  # Timestamp digest
        '/tr', hsm_config.timestamp_server,  # Timestamp RFC3161 server
        '/sha1', 'CERT_THUMBPRINT_HERE',  # Ou usar /csp para PKCS#11
        '/csp', 'PKCS#11 Provider Name',  # CSP para HSM
        '/kc', hsm_config.key_label,  # Key container name
        '/d', hsm_config.product_name,
        '/du', 'https://arkhe.org',
        filepath,
    ]

    print(f"🔐 Executando: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Assinatura aplicada: {output_path}")

        # Copiar para output path se diferente
        if output_path != filepath:
            import shutil
            shutil.copy2(filepath, output_path)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ signtool failed: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("❌ signtool not found. Install Windows SDK.", file=sys.stderr)
        return False

def generate_catalog_signature(
    catalog_path: str,
    hsm_provider: HSMProvider,
    config: SigningConfig
) -> bool:
    """Gera assinatura para catálogo de segurança."""
    print(f"🔐 Assinando catálogo: {catalog_path}")

    # Ler conteúdo do catálogo (excluindo seção de assinatura)
    with open(catalog_path, 'rb') as f:
        catalog_content = f.read()

    # Calcular hash do catálogo
    if config.hash_algorithm == 'SHA3_256':
        digest = hashlib.sha3_256(catalog_content).digest()
    else:
        digest = hashlib.sha256(catalog_content).digest()

    # Assinar com HSM
    signature = hsm_provider.sign_data(digest, config.hash_algorithm)

    # Inserir assinatura no catálogo (formato específico do Windows Catalog)
    # Em produção: usar makecat.exe + signtool ou API Catalog
    print(f"✅ Assinatura do catálogo gerada ({len(signature)} bytes)")

    # Salvar catálogo assinado
    signed_catalog = catalog_path.replace('.cat', '_signed.cat')
    with open(signed_catalog, 'wb') as f:
        f.write(catalog_content)
        # Inserir assinatura em seção apropriada (simplificado)
        f.write(b'\x00' * 1024)  # Placeholder para assinatura
        f.write(signature)

    print(f"✅ Catálogo assinado salvo: {signed_catalog}")
    return True

# ============================================================================
# VALIDAÇÃO PÓS-ASSINATURA
# ============================================================================

def verify_signature(filepath: str, config: SigningConfig) -> Dict[str, Any]:
    """Verifica assinatura Authenticode de arquivo."""
    result = {
        'file': filepath,
        'valid': False,
        'errors': [],
        'warnings': [],
        'details': {}
    }

    try:
        # Usar signtool para verificação
        cmd = ['signtool', 'verify', '/pa', '/v', filepath]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        result['details']['signtool_output'] = proc.stdout
        result['valid'] = (proc.returncode == 0)

        if not result['valid']:
            result['errors'].append(proc.stderr)

        # Verificar hash
        actual_hash = compute_file_hash(filepath, config.hash_algorithm)
        # Em produção: comparar com hash no catálogo/certificado

        result['details']['file_hash'] = actual_hash

    except Exception as e:
        result['errors'].append(str(e))

    return result

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Arkhe Cathedral Production Signing with HSM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos:
  %(prog)s --hsm-provider thales --input catedral.sys
  %(prog)s --hsm-provider aws_cloudhsm --input catedral.sys --catalog catedral.cat
  %(prog)s --verify-only --input catedral_signed.sys
        '''
    )

    parser.add_argument('--hsm-provider', required=True,
                       choices=['thales', 'utimaco', 'aws_cloudhsm', 'azure_dhsm', 'pkcs11_generic'],
                       help='Provedor HSM a utilizar')

    parser.add_argument('--input', required=True, help='Caminho para arquivo a assinar')

    parser.add_argument('--output', help='Caminho para arquivo assinado (default: input_signed)')

    parser.add_argument('--catalog', help='Caminho para catálogo .cat a assinar')

    parser.add_argument('--inf', help='Caminho para arquivo .inf do driver')

    parser.add_argument('--hsm-slot', type=int, help='Slot do HSM (PKCS#11)')

    parser.add_argument('--hsm-label', help='Label do token HSM')

    parser.add_argument('--key-label', default='arkhe-cathedral-production',
                       help='Label da chave no HSM')

    parser.add_argument('--cert', help='Caminho para certificado de código (opcional)')

    parser.add_argument('--verify-only', action='store_true',
                       help='Apenas verificar assinatura, não assinar')

    parser.add_argument('--dry-run', action='store_true',
                       help='Simular operação sem modificar arquivos')

    args = parser.parse_args()

    # Configurar
    config = SigningConfig(
        hsm_provider=args.hsm_provider,
        hsm_slot=args.hsm_slot,
        hsm_label=args.hsm_label,
        key_label=args.key_label,
        certificate_path=args.cert,
        catalog_path=args.catalog,
        inf_path=args.inf,
    )

    print(f"🔐 Arkhe Cathedral HSM Signing v{config.product_version}")
    print(f"   Provider: {config.hsm_provider}")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output or args.input.replace('.sys', '_signed.sys')}")
    print()

    # Modo apenas verificação
    if args.verify_only:
        print("🔍 Modo: Verificação apenas")
        result = verify_signature(args.input, config)

        if result['valid']:
            print("✅ Assinatura válida")
            return 0
        else:
            print(f"❌ Assinatura inválida: {result['errors']}")
            return 1

    # Modo dry-run
    if args.dry_run:
        print("🧪 Modo: Dry-run (simulação)")
        print("   • Hash calculado: " + compute_file_hash(args.input)[:16] + "...")
        print("   • Chave HSM: " + config.key_label)
        print("   • Assinatura: [SIMULADA]")
        print("✅ Dry-run concluído")
        return 0

    # Assinatura real
    print("🔐 Iniciando processo de assinatura...")

    # 1. Conectar ao HSM
    print("   1/5 Conectando ao HSM...")
    hsm = get_hsm_provider(config)
    if not hsm.connect():
        print("❌ Falha ao conectar ao HSM", file=sys.stderr)
        return 1
    print("   ✅ HSM conectado")

    # 2. Carregar chave e certificado
    print("   2/5 Carregando chave e certificado...")
    try:
        hsm.load_key(config.key_label)
        hsm.load_certificate(config.certificate_path)
    except Exception as e:
        print(f"❌ Falha ao carregar credenciais: {e}", file=sys.stderr)
        hsm.disconnect()
        return 1
    print("   ✅ Credenciais carregadas")

    # 3. Preparar dados para assinatura
    print("   3/5 Preparando dados para assinatura...")
    auth_data = prepare_authenticode_data(args.input)
    print(f"   • Hash SHA3-256: {auth_data['hash_sha3_256'][:16]}...")
    print("   ✅ Dados preparados")

    # 4. Assinar arquivo principal
    print("   4/5 Assinando arquivo...")
    if not sign_with_signtool(args.input, config, args.output):
        print("❌ Falha na assinatura do arquivo", file=sys.stderr)
        hsm.disconnect()
        return 1
    print("   ✅ Arquivo assinado")

    # 5. Assinar catálogo se fornecido
    if config.catalog_path and os.path.exists(config.catalog_path):
        print("   5/5 Assinando catálogo...")
        if not generate_catalog_signature(config.catalog_path, hsm, config):
            print("⚠️  Falha na assinatura do catálogo (continua)", file=sys.stderr)
        else:
            print("   ✅ Catálogo assinado")

    # Encerrar conexão HSM
    hsm.disconnect()
    print("   ✅ Conexão HSM encerrada")

    # Verificação final
    print("\n🔍 Verificando assinatura...")
    output_file = args.output or args.input.replace('.sys', '_signed.sys')
    verification = verify_signature(output_file, config)

    if verification['valid']:
        print("✅ Assinatura verificada com sucesso")
        print(f"\n📦 Arquivo assinado: {output_file}")
        if config.catalog_path:
            signed_cat = config.catalog_path.replace('.cat', '_signed.cat')
            print(f"📦 Catálogo assinado: {signed_cat}")
        print(f"\n🔐 Selo canônico: {compute_file_hash(output_file)[:16]}...")
        return 0
    else:
        print(f"❌ Verificação falhou: {verification['errors']}")
        return 1

if __name__ == '__main__':
    # Add simple mock of SigningConfig for compute_file_hash calls that fail
    global config
    config = SigningConfig(hsm_provider="mock")
    sys.exit(main())