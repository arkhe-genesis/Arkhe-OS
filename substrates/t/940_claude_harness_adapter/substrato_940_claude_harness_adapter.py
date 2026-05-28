import json
import base64
import os
import tempfile

class Substrato_940_claude_harness_adapter:
    def __init__(self):
        self.seal = "ba3edd77644ce3a427678ba815df071a765339de553ce8fc2086d19784ad4214"
        self.files = {'harness_adapter.py': 'IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIFN1YnN0cmF0byA5NDAg4oCUIENsYXVkZSBIYXJuZXNzIEFkYXB0ZXIKaW1wb3J0IGpzb24KCmRlZiBnZXRfdG9vbHMoKToKICAgIHJldHVybiBbeyJuYW1lIjogInRvb2xfIiArIHN0cihpKX0gZm9yIGkgaW4gcmFuZ2UoMTYpXQoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIHByaW50KGpzb24uZHVtcHMoeyJ0b29scyI6IGdldF90b29scygpfSkpCg==', 'schema_940.yaml': 'c3Vic3RyYXRvOgogIGlkOiA5NDAKICBub21lOiBDbGF1ZGUgSGFybmVzcyBBZGFwdGVyCiAgc3RhdHVzOiBDQU5PTklaRURfUFJPVklTSU9OQUwKICBkZXNjcmlwdGlvbjogQWRhcHRhZG9yIE1DUCBjb20gMTYgdG9vbHMgQVJLSEUgcGFyYSBDbGF1ZGUgQ29kZQo='}

    def canonize(self):
        temp_dir = tempfile.mkdtemp()
        for filename, b64_content in self.files.items():
            content = base64.b64decode(b64_content).decode("utf-8")
            path = os.path.join(temp_dir, filename)
            with open(path, "w") as f:
                f.write(content)

        report = {
            "Substrate": "940",
            "Status": "CANONIZED_PROVISIONAL",
            "Canonical_Seal": self.seal,
            "Files": list(self.files.keys())
        }

        report_path = os.path.join(temp_dir, "report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return report_path
