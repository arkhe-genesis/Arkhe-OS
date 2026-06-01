import json
import hashlib
import tempfile
import os

class Substrato896TelcoNFVBridge:
    def __init__(self):
        self.substrate_id = "896"
        self.substrate_name = "Telco-NFV Peptide Bridge"
        self.cross_links = ["900", "905", "895", "917"]

        self.payload_b64 = "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMyAKIyBzdWJzdHJhdGVfODk2X3RlbGNvX25mdl9icmlkZ2UucHkg4oCUIFN1YnN0cmF0ZSA4OTYgCiMgVGVsY28tTkZWIFBlcHRpZGUgQnJpZGdlOiBtb2RlbHMgTkZWL1NETiBhcyBwZXB0aWRlcyAmIGh5cGVyZ3JhcGggCiAKZnJvbSBkYXRhY2xhc3NlcyBpbXBvcnQgZGF0YWNsYXNzLCBmaWVsZCAKZnJvbSB0eXBpbmcgaW1wb3J0IERpY3QsIExpc3QsIE9wdGlvbmFsIAppbXBvcnQgaGFzaGxpYiwganNvbiwgcmVxdWVzdHMgCiAKQGRhdGFjbGFzcyAKY2xhc3MgVGVsY29ORlZQZXB0aWRlOiAKICAgICIiIk1vZGVscyBhIFZORi9DTkYgYXMgYSBwZXB0aWRlIGNvbmZvcm1pbmcgdG8gUGVwdGlkZeKAkVNhYVMgKDkwMCkuIiIiIAogICAgdm5mX2lkOiBzdHIgCiAgICB2bmZfdHlwZTogc3RyICAgICAgICAgICAgICAgIyBlLmcuLCAiVVBGIiwgIlNNRiIsICJBTUYiIAogICAgZGVzY3JpcHRvcjogRGljdFtzdHIsIGFueV0gICAjIEVUU0kgVk5GRCAKICAgIGVuZHBvaW50czogTGlzdFtzdHJdID0gZmllbGQoZGVmYXVsdF9mYWN0b3J5PWxpc3QpIAogICAgZGVmIHRvX3BlcHRpZGUoc2VsZikgLT4gRGljdDogCiAgICAgICAgcmV0dXJuIHsgCiAgICAgICAgICAgICJzZXF1ZW5jZSI6IHNlbGYudm5mX3R5cGUgKyAiOiIgKyBzZWxmLnZuZl9pZCwgCiAgICAgICAgICAgICJzb3VyY2VfY29kZV9oYXNoIjogaGFzaGxpYi5zaGEyNTYoanNvbi5kdW1wcyhzZWxmLmRlc2NyaXB0b3IpLmVuY29kZSgpKS5oZXhkaWdlc3QoKVs6MTZdLCAKICAgICAgICAgICAgImFwaV9lbmRwb2ludHMiOiB7ZXA6ICI1Zy0iICsgZXAgZm9yIGVwIGluIHNlbGYuZW5kcG9pbnRzfSwgCiAgICAgICAgICAgICJzdWJzY3JpcHRpb25fbW9kZWwiOiAiTUFOTy1saWNlbnNlIiAKICAgICAgICB9IAogCmNsYXNzIFRlbGNvSHlwZXJncmFwaE9yY2hlc3RyYXRvcjogCiAgICAiIiJNYXBzIHNlcnZpY2UgZnVuY3Rpb24gY2hhaW5zIGFzIGh5cGVyZWRnZXMuIiIiIAogICAgZGVmIF9faW5pdF9fKHNlbGYsIGh5cGVyZ3JhcGhfZW5kcG9pbnQpOiAKICAgICAgICBzZWxmLmhnID0gaHlwZXJncmFwaF9lbmRwb2ludCAKIAogICAgZGVmIGNoYWluX3NlcnZpY2Uoc2VsZiwgdm5mX2lkczogTGlzdFtzdHJdLCBjaGFpbl9uYW1lOiBzdHIsIG9yZGVyOiBMaXN0W2ludF0pOiAKICAgICAgICAiIiJDcmVhdGUgYSBoeXBlcmVkZ2UgcmVwcmVzZW50aW5nIGFuIG9yZGVyZWQgc2VydmljZSBjaGFpbi4iIiIgCiAgICAgICAgdmVydGljZXMgPSBbInZuZjoiICsgdmlkIGZvciB2aWQgaW4gdm5mX2lkc10gCiAgICAgICAgZWRnZSA9IHsgCiAgICAgICAgICAgICJlaWQiOiAic2ZjOiIgKyBjaGFpbl9uYW1lLCAKICAgICAgICAgICAgImV0eXBlIjogIlNlcnZpY2VGdW5jdGlvbkNoYWluIiwgCiAgICAgICAgICAgICJ2ZXJ0aWNlcyI6IHZlcnRpY2VzLCAKICAgICAgICAgICAgInByb3BlcnRpZXMiOiB7Im9yZGVyIjogb3JkZXJ9IAogICAgICAgIH0gCiAgICAgICAgcmVxdWVzdHMucG9zdChzZWxmLmhnICsgIi9oeXBlcmdyYXBoL2VkZ2UiLCBqc29uPWVkZ2UpIAogCiAgICBkZWYgaW1wb3J0X2Zyb21fZXRzaV9vc20oc2VsZiwgb3NtX3VybCk6IAogICAgICAgICIiIlB1bGwgVk5GIGRlc2NyaXB0b3JzIGZyb20gT1NNIGFuZCByZWdpc3RlciB0aGVtIGFzIHBlcHRpZGVzLiIiIiAKICAgICAgICAjIFBsYWNlaG9sZGVyIOKAkyBjYWxscyBPU00gQVBJIAogICAgICAgIHBhc3MgCg=="

    def canonize(self):
        # Specific strict-mode predefined seal requested in issue
        seal = "896-telco-nfv-peptide"

        data = {
            "Substrate": "{} - {}".format(self.substrate_id, self.substrate_name),
            "Status": "CANONIZED_PROVISIONAL",
            "Canonical_Seal": seal,
            "Files": {
                "substrate_896_telco_nfv_bridge.py": self.payload_b64
            }
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_896_")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        return path

if __name__ == "__main__":
    c = Substrato896TelcoNFVBridge()
    print(c.canonize())
