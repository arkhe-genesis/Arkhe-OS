import os
import base64
import json
import hashlib

def b64(text):
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')

# distro
sub_dir = "substrates/t/arkhe_distro_3_3_0"
os.makedirs(sub_dir, exist_ok=True)

with open(f"{sub_dir}/substrate.toml", "w") as f:
    f.write("""[substrate]
id = "distro-3.3.0"
name = "ARKHE-DISTRO v3.3.0"
status = "CANONIZED_PROVISIONAL"
""")

sub_py = """import os
import tempfile
import json
import base64
import hashlib

class SubstratoArkheDistro330:
    def __init__(self):
        self.substrate_id = "distro-3.3.0"
        self.status = "CANONIZED_PROVISIONAL"
        self.canonical_seal = "a7f3c9e1d2b4a5f6000000000000000000000000000000000000000000000000"
        self.b64_arkhe_distro_readme = "{arkhe_distro_readme}"
        self.b64_buf_gen_yaml = "{buf_gen_yaml}"

    def canonize(self):
        arkhe_distro_readme = base64.b64decode(self.b64_arkhe_distro_readme).decode("utf-8")
        buf_gen_yaml = base64.b64decode(self.b64_buf_gen_yaml).decode("utf-8")

        report = {{
            "Substrate": self.substrate_id,
            "Status": self.status,
            "Canonical_Seal": self.canonical_seal,
            "Files": {{
                "README.md": arkhe_distro_readme,
                "buf.gen.yaml": buf_gen_yaml
            }}
        }}

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(report, f)

        print("Report generated at: " + path)
        return path

if __name__ == "__main__":
    canon = SubstratoArkheDistro330()
    canon.canonize()
"""

readme = """## ARKHE-DISTRO v3.3.0 — Distribuição Canônica da Catedral

### Estrutura do Repositório

```
arkhe-distro/
├── README.md
├── LICENSE
├── SEAL.SHA3-256                  # Selo da distribuição completa
├── Makefile                       # Comandos de build, test, deploy
├── docker-compose.yml             # Ambiente de desenvolvimento completo
│
├── schemas/                       # 13 bundles YAML canônicos
│   ├── arkhe-common-v1.yaml
│   ├── temporalchain-v1.yaml
│   ├── epistemic-v1.yaml
│   ├── hermeszk-v1.yaml
│   ├── quicmesh-v1.yaml
│   ├── worldmodel-v1.yaml
│   ├── fluxmem-v1.yaml
│   ├── agency-v1.yaml
│   ├── brasilfinance-v1.yaml
│   ├── glasswing-v1.yaml
│   ├── mcpgateway-v1.yaml
│   ├── androidhal-v1.yaml
│   └── webgrounding-v1.yaml
│
├── proto/                         # Protobufs originais
│   └── arkhe/
│       ├── common/v1/header.proto
│       ├── temporalchain/v1/temporalchain.proto
│       ├── epistemic/v1/epistemic.proto
│       ├── hermeszk/v1/hermeszk.proto
│       ├── quicmesh/v1/quicmesh.proto
│       ├── worldmodel/v1/worldmodel.proto
│       ├── fluxmem/v1/fluxmem.proto
│       ├── agency/v1/agency.proto
│       ├── brasilfinance/v1/brasilfinance.proto
│       ├── glasswing/v1/glasswing.proto
│       ├── mcpgateway/v1/mcpgateway.proto
│       ├── androidhal/v1/androidhal.proto
│       └── webgrounding/v1/webgrounding.proto
│
├── gen/                           # Stubs gerados via buf
│   ├── go/                        # Go (github.com/arkhe-os/code-cathedral/gen/go)
│   ├── rust/                      # Rust (crates.io: arkhe-code-cathedral)
│   └── python/                    # Python (pip install arkhe-code-cathedral)
│
├── openapi/                       # 5 APIs REST
│   ├── temporalchain-openapi.yaml
│   ├── brasilfinance-openapi.yaml
│   ├── agency-openapi.yaml
│   ├── glasswing-openapi.yaml
│   └── mcpgateway-openapi.yaml
│
├── k8s/                           # 11 manifestos Kubernetes
│   ├── 00-namespace.yaml
│   ├── 01-rbac.yaml
│   ├── 02-configmap.yaml
│   ├── 03-secrets.yaml
│   ├── 10-temporalchain.yaml
│   ├── 11-quicmesh.yaml
│   ├── 12-hermeszk.yaml
│   ├── 13-brasilfinance.yaml
│   ├── 14-agency.yaml
│   ├── 20-ingress.yaml
│   ├── 30-hpa.yaml
│   └── 40-networkpolicy.yaml
│
├── helm/                          # Helm chart principal
│   └── arkhe-cathedral/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── terraform/                     # Infraestrutura como código
│   ├── main.tf
│   └── modules/
│       ├── oci/main.tf
│       ├── aws/main.tf
│       └── azure/main.tf
│
├── tests/                         # Testes E2E
│   └── e2e/
│       └── test_pix_zk_flow.py
│
├── buf.gen.yaml                   # Configuração do buf
├── prometheus-stack-values.yaml   # Observabilidade
└── grafana-dashboard.json         # Dashboard canônico
```
"""

buf_gen = """version: v2
managed:
  enabled: true
  override:
    - file_option: go_package_prefix
      value: github.com/arkhe-os/code-cathedral/gen/go
plugins:
  - remote: buf.build/protocolbuffers/go
    out: gen/go
    opt: paths=source_relative
  - remote: buf.build/grpc/go
    out: gen/go
    opt: paths=source_relative
  - remote: buf.build/protocolbuffers/python
    out: gen/python
  - remote: buf.build/grpc/python
    out: gen/python
  - remote: buf.build/community/neoeinstein-prost
    out: gen/rust
    opt:
      - compile_well_known_types
      - extern_path=.google.protobuf=::pbjson_types
"""

with open(f"{sub_dir}/substrato_arkhe_distro.py", "w") as f:
    f.write(sub_py.format(
        arkhe_distro_readme=b64(readme),
        buf_gen_yaml=b64(buf_gen)
    ))
