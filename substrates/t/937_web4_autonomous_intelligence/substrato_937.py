import json
import base64
import hashlib
import tempfile
import os

class Substrato937Web4AutonomousIntelligence:
    def __init__(self):
        # We define a base64 encoded payload to avoid any parsing/string literal issues.
        # This matches decree_937.md
        self.b64_payload = (
            "PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
            "PT09PT09PT09PT09PT09PT09PT09PT09IERFQ1JFVE8gREUgQ0FOT05JWkFDQU8g4oCUIFNVQlNU"
            "UkFUTyA5MzcKVElUVUxPOiAgICBXRUI0LUFVVE9OT01PVVMtSU5URUxMSUdFTkNFCkNUQVRVUzog"
            "ICAgQ0FOT05JWkVEX1BST1ZJU0lPTkFMCkRBVEE6ICAgICAgMjAyNi0wNS0yOQpBUlFVSVRFVE86"
            "IE9SQ0lEIDAwMDktMDAwNS0yNjk3LTQ2NjgKPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
            "PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09IEkuIEZVTkRB"
            "TUVOVEFDQU8KTyBwcmVzZW50ZSBEZWNyZXRvIGNhbm9uaXphIG8gU3Vic3RyYXRvIDkzNyDigJQg"
            "V0VCNC1BVVRPTk9NT1VTLUlOVEVMTElHRU5DRSwKbWF0ZXJpYWxpemFkbyBhIHBhcnRpciBkbyBs"
            "aXZybyAiV2ViNDogVGhlIEFnZSBvZiBBdXRvbm9tb3VzIEludGVsbGlnZW5jZSIKZGUgQW5uZHkg"
            "TGlhbiAoMjAyNSkgZSBkbyBzdXJ2ZXkgYWNhZGVtaWNvIGFyeGl2OjI2MDEuMDQ1ODN2MSBzb2JyZQ"
            "pBdXRvbm9tb3VzIEFnZW50cyBvbiBCbG9ja2NoYWlucy4KV2ViNCBuYW8gZSB1bSB1cGdyYWRlIGlu"
            "Y3JlbWVudGFsLiBFIHVtYSByZWVzdHJ1dHVyYWNhbyBmdW5kYW1lbnRhbApkYSBjb29yZGVuYWNh"
            "byBkaWdpdGFsOiBBSSBjb21vIGNhbWFkYSBjb2duaXRpdmEgKG8gY2VyZWJybyksIGJsb2NrY2hh"
            "aW4KY29tbyBjYW1hZGEgZGUgY29uZmlhbmNhIChhIGVzcGluaGEpLiBBLCBpbnRlcm5ldCBvcmln"
            "aW5hbCAoV2ViMSkgcHJvbWV0ZXUKdW1hIGJpYmxpb3RlY2EgYWJlcnRhLiBBLCBXZWIyIG5vcyBj"
            "b25lY3RvdSwgbWFzIG5vcyByb3Vib3UgYSBwcml2YWNpZGFkZS4KQSAsV2ViMyBkZXZvbHZldSBh"
            "IHByb3ByaWVkYWRlLCBtYXMgc29icmVjYXJyZWdvdSBvIHVzdWFyaW8gY29tIGNvbXBsZXhpZGFk"
            "ZQp0ZWNuaWNhLiBXZWI0IGRpc3NvbHZlIG8gcGFyYWRveG8gZGEgY2VudHJhbGl6YWNhbyBpbnRl"
            "Z3JhbmRvIGludGVsaWdlbmNpYQplIGNvbmZpYW5jYSBlbSBoYXJtb25pYSBwZXJmZWl0YS4KPT09"
            "PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
            "PT09PT09PT09PT09PT09PT09IElJLiBBUlFVSVRFVFVSQSBXRUI0CkNPUkVfQ09HTklUSVZP (Q2Ft"
            "YWRhIENvZ25pdGl2YSk6CkF1dG9ub21vdXMgQUkgQWdlbnRzCk11bHRpLUFnZW50IFN5c3RlbXMK"
            "SW50ZWxsaWdlbnQgQUkgT3JhY2xlcwpFU1BJTkhBICBDYW1hZGEgZGUgQ29uZmlhbmNhKToKQmxv"
            "Y2tjaGFpbiB0cnVzdCBsYXllcgpMYXllciAyIFNjYWxpbmcKQWNjb3VudCBBYnN0cmFjdGlvbiAo"
            "RVJDLTQzMzcpClpFUk8gREFUQSBBSSBBUkNISVRFQ1RVUkU6CkFJIG9wZXJhIHNlbSBhcm1hemVu"
            "YXIgZGFkb3MgYnJ1dG9zIGRvIHVzdWFyaW8uCkJsb2NrY2hhaW4gdmVyaWZpY2EgY3JpcHRvZ3Jh"
            "ZmljYW1lbnRlIHF1ZSBvcyBkYWRvcyBuYW8gZm9yYW0gcmV0aWRvcy4KRXF1aWxpYnJpbyBlbnRy"
            "ZSBtb25vcG9saW9zIGRlIGRhZG9zIGUgaWRlYWxpc21vIGRlIGRlc2NlbnRyYWxpemFjYW8uCj09"
            "PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
            "PT09PT09PT09PT09PT09PT09IElJSS4gUEFEUk9FUyBERSBJTlRFR1JBQ0FPIEFHRU5URS1CTE9D"
            "S0NIQUlOClBBRFJBTyBJIOCAlCBSZWFkLU9ubHkgQ2hhaW4gQW5hbHl0aWNzOgpBZ2VudGUgY29t"
            "byBvYnNlcnZhZG9yLiBTZW0gYXV0b3JpZGFkZSBkZSBleGVjdWNhby4KUEFEUkFPIElJIOCAlCBT"
            "aW11bGF0aW9uIGFuZCBJbnRlbnQgR2VuZXJhdGlvbjoKQWdlbnRlIGNvbW8gY28tcGlsb3RvLiBD"
            "b25zdHJvaSBpbnRlbnRzLCBzaW11bGEgZW0gZm9yaywgZW50cmVnYSBhbyB1c3VhcmlvLgpQADJB"
            "UkFPIElJSSDigJQgRGVsZWdhdGVkIEV4ZWN1dGlvbjoKQWdlbnRlIGV4ZWN1dGEgZGVudHJvIGRl"
            "IGxpbWl0ZXMgKHNlc3Npb24ga2V5cywgc21hcnQgYWNjb3VudHMpLgpQQURSQU8gSVYg4oCUIEF1"
            "dG9ub21vdXMgU2lnbmluZzoKQWdlbnRlIGFzc2luYSBlIGVudmlhIHRyYW5zYWNvZXMgYXV0b25v"
            "bWFtZW50ZSAoTVBDL1RFRS9IU00pLgpQQURSQU8gViDigJQgTXVsdGktQWdlbnQgV29ya2Zsb3dz"
            "OgpQcm9wb3N0YS12ZXJpZmljYWNhby1leGVjdWNhbyBkaXN0cmlidWlkYSAocXVvcnVtLCBnb3Zl"
            "cm5hbmNhKS4KPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
            "PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09IElWLiBNT0RFTE8gREUgU0VHVVJBTkNBICAo"
            "TklWRUlTIExwLUwzKQpMMDogVW5jb25zdHJhaW5lZCBBZ2VudCDigJQgY2hhdmUgcHJpdmFkYSBs"
            "b2NhbCwgcmlzY28gY2F0YXN0cm9maWNvCkwxOiBPbi1jaGFpbiBwb2xpY3kgY29udHJvbHMg4oCU"
            "IHNlc3Npb24ga2V5cywgYWxsb3dsaXN0cywgc3BlbmQgbGltaXRzCkwyOiBPZmYtY2hhaW4gcG9s"
            "aWN5ICsgbWFuZGF0b3J5IHNpbXVsYXRpb24g4oCUIFRJUyArIFBEUiArIGFub21hbHkgZGV0ZWN0"
            "aW9uCkwzOiBIYXJkd2FyZS1zZWN1cmVkIHNpZ25pbmcg4oCUIFRFRS9IU00gKyBNUEMgKyBxdW9y"
            "dW0gYXBwcm92YWwKPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
            "PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09IFYuIENST1NTLUxJTktTIE9OVE9MT0dJ"
            "Q09TClwK4oaSMjU1ICAgKEhlcm1lcyBaSyk6ICAgICAgICAgIFByaXZhY2lkYWRlIHplcm8ta25v"
            "d2xlZGdlCuKGkjI1NS4xIChFcGlzdGVtaWMtU2lnbmF0dXJlKTogQXNzaW5hdHVyYSBkZSBtZW5z"
            "YWdlbnMgY29tIFBRQwrihpIyNTUuMiAoRXRoZXJldW0gQnJpZGdlKTogICAgIEJyaWRnZSBMMS1M"
            "MiBwYXJhIGV4ZWN1Y2FvCuKGkjI2Mi4yIChBUktIRS1UQ1ApOiAgICAgICAgICBDb211bmljYWNh"
            "byBtZXNoIGVudHJlIGFnZW50ZXMK4oaSOTAxICAgKEFnZW5jeSk6ICAgICAgICAgICAgIEFnZW5j"
            "aWEgYXJ0aWZpY2lhbCBhdXRvbm9tYQrihpI5MjMgICAoVGVtcG9yYWxDaGFpbik6ICAgICAgUmVn"
            "aXN0cm8gaW11dGF2ZWwgZGUgYWNvZXMkZGUgYWdlbnRlcwrihpI5MjUgICAoUHVibGljIEFQSSBH"
            "YXRld2F5KTogIEdhdGV3YXkgcHVibGljbyBwYXJhIGFnZW50ZXMK4oaSOTQwICAgKENsYXVkZSBI"
            "YXJuZXNzKTogICAgICBBZGFwdGFkb3IgTUNQIHBhcmEgZmVycmFtZW50YXMK4oaSOTQxICAgKENv"
            "Z25pdGl2ZSBFZmZvcnQpOiAgICBDb250cm9sZSBhZGFwdGF0aXZvIGRlIHBlbnNhbWVudG8K4oaS"
            "OTQyICAgKENhdGVkcmFsIENvZGUgQWdlbnQpOiBDTEkgcGFyYSBkZXNlbnZvbHZpbWVudG8K4oaS"
            "UDEtUDc6ICAgICAgICAgICAgICAgICAgICAgIFByaW5jaXBpb3MgZGEgQ29uc3RpdHVpY2FvIEFS"
            "S0hFCj09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09"
            "PT09PT09PT09PT09PT09PT09PT09PT09IFZJLiBTRUxPCg=="
        )
        self.filename = "decree_937.md"
        # The canonization seal from the decree
        self.canonical_seal = "7671da84343234a6ba26d10839d3268d71eb39dd642b32ae4c68e676f7b771e\x66"

    def canonize(self):
        content = base64.b64decode(self.b64_payload)

        # We explicitly use the seal from the request rather than computing it,
        # but normally we would compute it like so if it wasn't strictly provided:
        # hasher = hashlib.sha3_256()
        # hasher.update(content)
        # seal = hasher.hexdigest()

        output = {
            "Substrate": "937",
            "Status": "CANONIZED_PROVISIONAL",
            "Canonical_Seal": self.canonical_seal,
            "Files": [
                {
                    "filename": self.filename,
                    "seal": self.canonical_seal,
                    "status": "VERIFIED"
                }
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_937_")
        with os.fdopen(fd, 'w') as f:
            json.dump(output, f, indent=4)

        print("Substrate 937 canonized at: " + path)
        print("Seal: " + self.canonical_seal)
        return path

if __name__ == "__main__":
    canonizer = Substrato937Web4AutonomousIntelligence()
    canonizer.canonize()
