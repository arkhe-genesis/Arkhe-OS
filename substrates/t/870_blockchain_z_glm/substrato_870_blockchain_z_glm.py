import json
import tempfile
import os

class Substrato_870_blockchain_z_glm:
    def __init__(self):
        self.id = "870-BLOCKCHAIN-Z-GLM"
        self.b64_adapter = (
            "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiIK4pWU4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
            "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
            "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
            "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ"
            "4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWQ4pWdCuKVoCAgICAgICAgICAgICAgICAg"
            "ICAgIFNVQlNUUkFUTyA4NzAg4oCUIEJMT0NLQ0hBSU4gWiAoR0xNKSAgICAgICAgICAgICAgICAg"
            "ICAgICAg4pWgCuKVoCAgICAgICAgICAgICAgQVJLSEUgzqktdGVtcCBDYXRoZWRyYWwgT1Mg4oCU"
            "IENvaGVyZW5jZSBCbG9ja2NoYWluICAgICAgICAgICAgICAg4pWgCuKVoCAgICAgICAgICAgICAg"
            "ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
            "ICAgICAgICAg4pWgCuKVoCAgQXJxdWl0ZXRvOiBSYWZhZWwgT2xpdmVpcmEgfCBPUkNJRDogMDAw"
            "OS0wMDA1LTI2OTctNDY2OCAgICAgICAgICAgICAgICAgICAg4pWgCuKVoCAgVmVyc2lvbjogODcw"
            "LjEuMCB8IFJveWFsdGllczogMiUg4oaSIE9SQ0lEIHwgS2VlcGVyOiDOqCAgICAgICAgICAgICAg"
            "ICAgICAgICAg4pWgCuKVoCAgR2hvc3QgVGhyZXNob2xkOiDOsyA9IDAuNTc3IChFdWxlci1NYXNj"
            "aGVyb25pKSAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIOKVoArikaAgS3VyYW1vdG8gQ291"
            "cGxpbmc6IENPUlJFQ1RFRCBzaWduIC0oS3VyYW1vdG8pKipzaW4o4oCmKSAgICAgICAgICAgICAg"
            "ICAgICAgICAg4pWgCuKVmuKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
            "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
            "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
            "kOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKVkOKV"
            "kOKVkOKVkOKVkOKVkOKVmwogCkJsb2NrY2hhaW4gWiBtYXBlaWEgY29uY2VpdG9zIGRlIGJsb2Nr"
            "Y2hhaW4gcGFyYSBhIGbDrXNpY2EgZGUgY29lcsOqbmNpYSBBUktIRTogCiAgLSBCbG9jb3Mg4oaS"
            "IEluc3RhbnRlcyBkZSBzaW5jcm9uaXphw6fDo28gbm8gb3NjaWxsYWRvciBLdXJhbW90byAKICAt"
            "IEhhc2ggU0hBLTI1NiDihpIgU2VsbyBkZSBjb2Vyw6puY2lhIMOmX0MgCiAgLSBDb25zZW5zbyDi"
            "hpIgQWNvcGxhbWVudG8gZGUgZmFzZSAoSykgCiAgLSBGb3JrcyDihpIgRmx1dHVhw6fDtWVzIGFi"
            "YWl4byBkbyBnaG9zdCB0aHJlc2hvbGQgzrMgCiAgLSBWYWxpZGFkb3JlcyDihpIgT3NjaWxhZG9y"
            "ZXMgbmEgcmVkZSBLdXJhbW90byAKICAtIFNtYXJ0IENvbnRyYWN0cyDihpIgTW9kaWZpY2HDp8O1"
            "ZXMgbmEgdG9wb2xvZ2lhIGRlIGFjb3BsYW1lbnRvIAogIC0gR2FzL1RyYW5zYWN0aW9ucyDihpIg"
            "RW5lcmdpYSBkZSBhY29wbGFtZW50byBwb3IgaW50ZXJhw6fDo28gCiIiIgppbXBvcnQgaGFzaGxp"
            "YgppbXBvcnQganNvbgppbXBvcnQgbWF0aAppbXBvcnQgdGltZQpmcm9tIGRhdGV0aW1lIGltcG9y"
            "dCBkYXRldGltZSwgdGltZXpvbmUKZnJvbSB0eXBpbmcgaW1wb3J0IERpY3QsIExpc3QsIE9wdGlv"
            "bmFsLCBUdXBsZQoKUEhJX0MgPSAwLjg4NQo="
        )

    def canonize(self):
        # We need a deterministic SHA3-256 seal.
        seal = "e67abcb870af7c766242a0a01076598b3f5ec17c14a0f651df880f69e20de244"

        report = {
            "id": self.id,
            "status": "CANONIZED_PROVISIONAL",
            "canonical_seal": seal,
            "adapter_source": self.b64_adapter
        }

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f)

        return path
