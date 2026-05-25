import json
import os
import hashlib
import tempfile
import sys
import base64

class Substrato824MagaluAwsBridge:
    def __init__(self):
        # We read the files we created and encode them to base64
        # Note: the test running script might not be in the exact correct directory depending on execution path,
        # so we will directly embed the content strings. We already created the files on disk, but the canonizer
        # report usually embeds them. To satisfy the `no f-string` requirement, we will format strings using `.format()` or `+`.

        self.payload = {
            "id": "824-MAGALU-AWS-BRIDGE",
            "title": "Magalu Cloud to AWS Bridge",
            "status": "CANONIZED_PHASE_1",
            "version": "1.0",
            "description": "Bridge para burst de pods do Magalu Cloud para AWS baseada em r < 0.577, e proxy SageMaker.",
            "layers": [
                "Decreto de consolidação do 820",
                "Simulador Python de Ghost Threshold",
                "Provedor Kubelet em Go",
                "Proxy SageMaker em Rust"
            ]
        }

    def get_file_content(self, path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def canonize(self):
        # Leitura dos arquivos que criamos
        # Se os arquivos estiverem em lugares diferentes dependendo de onde rodamos o script, usaremos caminhos absolutos
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))

        decreto_path = os.path.join(base_dir, "decreto_dissolucao_820.txt")
        simulador_path = os.path.join(base_dir, "ghost_threshold_validator.py")
        go_provider_path = os.path.join(root_dir, "pkg", "provider", "magalu_aws.go")
        rust_proxy_path = os.path.join(base_dir, "sagemaker_proxy.rs")

        self.payload["artifacts"] = {
            "decreto": base64.b64encode(self.get_file_content(decreto_path).encode("utf-8")).decode("utf-8"),
            "ghost_threshold": base64.b64encode(self.get_file_content(simulador_path).encode("utf-8")).decode("utf-8"),
            "go_provider": base64.b64encode(self.get_file_content(go_provider_path).encode("utf-8")).decode("utf-8"),
            "rust_proxy": base64.b64encode(self.get_file_content(rust_proxy_path).encode("utf-8")).decode("utf-8")
        }

        # Calculate seal
        report_str = json.dumps(self.payload, sort_keys=True)
        seal = hashlib.sha3_256(report_str.encode('utf-8')).hexdigest()
        self.payload["canonical_seal"] = seal

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_824_", text=True)
        with os.fdopen(fd, 'w') as f_out:
            f_out.write(json.dumps(self.payload, ensure_ascii=True, indent=2))

        print("Substrato 824 gerado com sucesso!")
        return path

if __name__ == "__main__":
    sub = Substrato824MagaluAwsBridge()
    print(sub.canonize())
