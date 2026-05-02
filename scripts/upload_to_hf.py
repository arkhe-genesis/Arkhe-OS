from huggingface_hub import HfApi, create_repo
from pathlib import Path
import json

def upload_arkhe_onnx_models(
    repo_id: str = "arkhe-os/crystal-brain-onnx",
    model_dir: str = "arkhe-onnx-web/models",
    token: str = None
):
    """Publica modelos ONNX do ARKHE no Hugging Face Hub."""

    api = HfApi(token=token)

    # Criar repositório se não existir
    try:
        create_repo(repo_id, repo_type="model", private=False, exist_ok=True)
        print(f"✅ Repo {repo_id} ready")
    except Exception as e:
        print(f"⚠️  Repo may already exist: {e}")

    # Arquivos para upload
    files_to_upload = [
        f"{model_dir}/crystal_sae.onnx",
        f"{model_dir}/wigner_approx.onnx",
        "arkhe-onnx-web/config.json",
        "arkhe-onnx-web/README.md",
        "arkhe-onnx-web/metadata.json",
    ]

    # Upload de cada arquivo
    for file_path in files_to_upload:
        if Path(file_path).exists():
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=Path(file_path).name,
                repo_id=repo_id,
                repo_type="model"
            )
            print(f"📤 Uploaded: {file_path}")
        else:
            print(f"⚠️  Not found: {file_path}")

    # Upload de exemplos
    examples_dir = Path("arkhe-onnx-web/examples")
    if examples_dir.exists():
        for example in examples_dir.glob("*"):
            api.upload_file(
                path_or_fileobj=str(example),
                path_in_repo=f"examples/{example.name}",
                repo_id=repo_id,
                repo_type="model"
            )
            print(f"📤 Uploaded example: {example.name}")

    print(f"\n🎉 Models published: https://huggingface.co/{repo_id}")
    return repo_id

if __name__ == "__main__":
    import os
    token = os.environ.get("HF_TOKEN")  # Definir via variável de ambiente
    upload_arkhe_onnx_models(token=token)
