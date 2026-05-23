import json
import tempfile
import os

class SubstratoEngPractices:
    def canonize(self):
        report = {
            "Title": "Google Engineering Practices",
            "Description": "Google's Engineering Practices documentation",
            "Components": [
                "The Code Reviewer's Guide",
                "The Change Author's Guide"
            ],
            "Terminology": {
                "CL": "Changelist, meaning one self-contained change",
                "LGTM": "Looks Good to Me"
            },
            "License": "CC-By 3.0",
            "Repository": "https://github.com/google/eng-practices"
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_eng_practices_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Google Engineering Practices. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoEngPractices()
    substrate.canonize()
