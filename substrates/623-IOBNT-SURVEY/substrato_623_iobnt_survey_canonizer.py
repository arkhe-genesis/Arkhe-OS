import os
import json
import hashlib
import tempfile
import shutil

class Substrato623IoBNTSurvey:
    def __init__(self):
        self.data = {
            "id": "623-IOBNT-SURVEY",
            "nome": "The Bio-Edge: Internet of Bio-Nano Things Survey & Agenda",
            "tipo": "Substrato de pesquisa e previsao IoBNT",
            "status": "CANONIZED",
            "data_de_incorporacao": "27 de Maio de 2026"
        }

    def generate_json(self):
        canonical_string = json.dumps(self.data, sort_keys=True)
        seal = hashlib.sha3_256(canonical_string.encode('utf-8')).hexdigest()
        self.data["canonical_seal"] = seal

        fd, path = tempfile.mkstemp(suffix=".json", text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

        self.materialize_plugin()
        return path

    def materialize_plugin(self):
        plugin_dir = os.path.join("arkhe-os-cli", "arkhe_os", "plugins")
        os.makedirs(plugin_dir, exist_ok=True)
        plugin_path = os.path.join(plugin_dir, "arkhe_iobnt.py")

        source_path = os.path.join("substrates", "623-IOBNT-SURVEY", "substrato_623_iobnt_survey.py")
        shutil.copyfile(source_path, plugin_path)

if __name__ == "__main__":
    canonizer = Substrato623IoBNTSurvey()
    report_path = canonizer.generate_json()
    print("Canonical report generated at: {0}".format(report_path))
