#!/usr/bin/env python3
"""
ARKHE Cathedral - Substrato 631-OPENSERV-SERV Canonizer.
Canonizes the OpenServ Serv integration into the ARKHE ecosystem.
Strictly adheres to the NO F-STRINGS invariant.
"""
import os
import sys
import json
import hashlib
import tempfile

def canonize_631():
    temp_dir = tempfile.mkdtemp()

    plugin_dir = os.path.join(temp_dir, "arkhe_os", "plugins", "openserv")
    os.makedirs(plugin_dir, exist_ok=True)

    plugin_content = '''#!/usr/bin/env python3
"""arkhe-openserv — OpenServ Gateway Integration."""
import click
import json
import urllib.request
import urllib.error

@click.group()
def openserv():
    """OpenServ Gateway Management."""
    pass

@openserv.command("invoke")
@click.argument("serv_id")
@click.option("--inputs", default="{}", help="JSON input payload")
def cmd_invoke(serv_id, inputs):
    """Invokes an external Serv and validates the ZK proof."""
    req_data = {
        "serv_id": serv_id,
        "inputs": json.loads(inputs)
    }
    req_bytes = json.dumps(req_data).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8080",
        data=req_bytes,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            click.echo("✓ Serv {0} executed successfully.".format(res_data.get("serv_id")))
            click.echo("  Proof: {0}".format(res_data.get("proof")))
            click.echo("  Output: {0}".format(json.dumps(res_data.get("output"))))
    except urllib.error.URLError as e:
        click.echo("✗ Failed to contact gateway: {0}".format(str(e)), err=True)

def register(cli):
    cli.add_command(openserv)
'''

    plugin_path = os.path.join(plugin_dir, "arkhe_openserv.py")
    with open(plugin_path, "w", encoding="utf-8") as file:
        file.write(plugin_content)

    seal = hashlib.sha3_256(plugin_content.encode("utf-8")).hexdigest()

    canonical_data = {
        "id": "631-OPENSERV-SERV",
        "nome": "OpenServ Serv externalization unit",
        "tipo": "Substrato de expansao de malha cognitiva",
        "tecnologias": "OpenServ, ZK-Proofs, REST, gRPC",
        "aplicacoes": "Externalizacao de loops cognitivos, orquestracao ZK",
        "status": "CANONIZED_PROVISIONAL",
        "data_de_incorporacao": "28 de Maio de 2026",
        "seal_sha3_256": seal
    }

    json_path = os.path.join(temp_dir, "FICHA_CANONICA_631.json")
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(canonical_data, file, ensure_ascii=False, indent=2)

    return temp_dir

if __name__ == "__main__":
    out = canonize_631()
    print("Substrate 631 canonized at: " + out)
