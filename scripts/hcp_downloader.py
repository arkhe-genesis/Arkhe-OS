#!/usr/bin/env python3
"""
hcp_downloader.py
Script auxiliar para download automatizado de dados HCP-Aging.
"""

import boto3
import argparse
from pathlib import Path
import json

def setup_credentials():
    """Configura credenciais interativamente"""
    print("Configuração de acesso HCP-Aging")
    print("Obtenha suas chaves em: https://db.humanconnectome.org")

    access_key = input("Access Key ID: ")
    secret_key = input("Secret Access Key: ")

    creds = {
        'access_key': access_key,
        'secret_key': secret_key
    }

    cred_file = Path.home() / '.hcp_credentials.json'
    with open(cred_file, 'w') as f:
        json.dump(creds, f)

    print(f"Credenciais salvas em {cred_file}")
    return cred_file

def download_subject(subject_id: str, output_dir: Path, cred_file: Path):
    """Baixa dados estruturais de um sujeito"""
    if not cred_file.exists():
        print(f"Erro: Arquivo de credenciais não encontrado em {cred_file}")
        return

    with open(cred_file) as f:
        creds = json.load(f)

    s3 = boto3.client('s3',
        aws_access_key_id=creds['access_key'],
        aws_secret_access_key=creds['secret_key']
    )

    bucket = 'hcp-openaccess'
    subj_dir = output_dir / subject_id / "V1"
    subj_dir.mkdir(parents=True, exist_ok=True)

    # Arquivos prioritários (estruturais)
    files_to_download = [
        (f"HCP_Aging/{subject_id}/T1w/Diffusion/connectome.csv", "structural_connectome.csv"),
        (f"HCP_Aging/{subject_id}/T1w/Diffusion/nodes.nii.gz", "nodes.nii.gz"),
    ]

    for s3_key, local_name in files_to_download:
        local_file = subj_dir / local_name
        if local_file.exists():
            print(f"✓ {local_file.name} já existe")
            continue

        try:
            print(f"Baixando {s3_key}...")
            s3.download_file(bucket, s3_key, str(local_file))
        except Exception as e:
            print(f"✗ Erro: {e}")

def download_metadata(output_dir: Path, cred_file: Path):
    """Baixa metadados comportamentais (unrestricted.csv)"""
    if not cred_file.exists():
        print(f"Erro: Arquivo de credenciais não encontrado em {cred_file}")
        return

    with open(cred_file) as f:
        creds = json.load(f)

    s3 = boto3.client('s3',
        aws_access_key_id=creds['access_key'],
        aws_secret_access_key=creds['secret_key']
    )

    bucket = 'hcp-openaccess'
    s3_key = "HCP_Aging/Behavioral/unrestricted.csv"
    local_file = output_dir / "hcp_aging_behavior.csv"

    if local_file.exists():
        print(f"✓ {local_file.name} já existe")
        return

    try:
        print(f"Baixando metadados {s3_key}...")
        s3.download_file(bucket, s3_key, str(local_file))
    except Exception as e:
        print(f"✗ Erro ao baixar metadados: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download HCP-Aging data")
    parser.add_argument("--setup", action="store_true", help="Configure credentials")
    parser.add_argument("--metadata", action="store_true", help="Download behavioral metadata")
    parser.add_argument("--subject", type=str, help="Subject ID (e.g., HCA6002236)")
    parser.add_argument("--output", type=str, default="/data/hcp_aging",
                       help="Output directory")
    parser.add_argument("--credentials", type=str,
                       default="~/.hcp_credentials.json")

    args = parser.parse_args()

    if args.setup:
        setup_credentials()
    elif args.metadata:
        download_metadata(
            Path(args.output),
            Path(args.credentials).expanduser()
        )
    elif args.subject:
        download_subject(
            args.subject,
            Path(args.output),
            Path(args.credentials).expanduser()
        )
    else:
        parser.print_help()
