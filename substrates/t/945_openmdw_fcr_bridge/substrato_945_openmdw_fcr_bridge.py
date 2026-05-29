import os
import json
import base64
import hashlib

class Substrato945OpenMDWFCRBridge:
    def __init__(self):
        self.bridge_payload = "aW1wb3J0IGhhc2hsaWIKaW1wb3J0IGpzb24KCmNsYXNzIE9wZW5NRFdMaWNlbnNlOgogICAgZGVmIF9faW5pdF9fKHNlbGYsIHZlcnNpb249IjEuMSIpOgogICAgICAgIHNlbGYudmVyc2lvbiA9IHZlcnNpb24KCiAgICBkZWYgdmVyaWZ5X2xpY2Vuc2Uoc2VsZiwgbW9kZWxfbWF0ZXJpYWxzKToKICAgICAgICAjIFNpbXVsYXRlcyBjaGVja2luZyBpZiBtb2RlbCBtYXRlcmlhbHMgY29tcGx5IHdpdGggT3Blbk1EVyB2MS4xCiAgICAgICAgaGFzaF9vYmogPSBoYXNobGliLnNoYTNfMjU2KGpzb24uZHVtcHMobW9kZWxfbWF0ZXJpYWxzLCBzb3J0X2tleXM9VHJ1ZSkuZW5jb2RlKCJ1dGYtOCIpKQogICAgICAgIGxpY2Vuc2VfaGFzaCA9IGhhc2hfb2JqLmhleGRpZ2VzdCgpCiAgICAgICAgcmV0dXJuIHsKICAgICAgICAgICAgImNvbXBsaWFudCI6IFRydWUsCiAgICAgICAgICAgICJ2ZXJzaW9uIjogc2VsZi52ZXJzaW9uLAogICAgICAgICAgICAibGljZW5zZV9oYXNoIjogbGljZW5zZV9oYXNoCiAgICAgICAgfQoKY2xhc3MgRkNSU2ltdWxhdG9yQnJpZGdlOgogICAgZGVmIF9faW5pdF9fKHNlbGYsIGxpY2Vuc2VfbWFuYWdlcik6CiAgICAgICAgc2VsZi5saWNlbnNlX21hbmFnZXIgPSBsaWNlbnNlX21hbmFnZXIKCiAgICBkZWYgaW5qZWN0X2Zjcl9vdXRwdXQoc2VsZiwgc2xvdCwgZW5naW5lX25hbWUsIG1vZGVsX21hdGVyaWFscyk6CiAgICAgICAgbGljZW5zZV9pbmZvID0gc2VsZi5saWNlbnNlX21hbmFnZXIudmVyaWZ5X2xpY2Vuc2UobW9kZWxfbWF0ZXJpYWxzKQogICAgICAgIGlmIG5vdCBsaWNlbnNlX2luZm8uZ2V0KCJjb21wbGlhbnQiKToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiTW9kZWwgbWF0ZXJpYWxzIGRvIG5vdCBjb21wbHkgd2l0aCBPcGVuTURXIGxpY2Vuc2UuIikKICAgICAgICAKICAgICAgICByZXR1cm4gewogICAgICAgICAgICAic2xvdCI6IHNsb3QsCiAgICAgICAgICAgICJlbmdpbmVfbmFtZSI6IGVuZ2luZV9uYW1lLAogICAgICAgICAgICAiZmFzdF9jb25maXJtZWQiOiBUcnVlLAogICAgICAgICAgICAibGljZW5zZV9oYXNoIjogbGljZW5zZV9pbmZvLmdldCgibGljZW5zZV9oYXNoIikKICAgICAgICB9CgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAgbGljZW5zZV9tZ3IgPSBPcGVuTURXTGljZW5zZSgpCiAgICBicmlkZ2UgPSBGQ1JTaW11bGF0b3JCcmlkZ2UobGljZW5zZV9tZ3IpCiAgICAKICAgIG1vY2tfbWF0ZXJpYWxzID0geyJtb2RlbF93ZWlnaHRzIjogImNvbXBsaWFudCIsICJkb2N1bWVudGF0aW9uIjogImNjLWJ5LTQuMCJ9CiAgICBvdXRwdXQgPSBicmlkZ2UuaW5qZWN0X2Zjcl9vdXRwdXQoc2xvdD00MzUwMDAsIGVuZ2luZV9uYW1lPSJsaWdodGhvdXNlIiwgbW9kZWxfbWF0ZXJpYWxzPW1vY2tfbWF0ZXJpYWxzKQogICAgcHJpbnQoanNvbi5kdW1wcyhvdXRwdXQsIGluZGVudD0yKSkK"
        self.toml_payload = "W3N1YnN0cmF0ZV0KbmFtZSA9ICI5NDUtT1BFTk1EVy1GQ1ItQlJJREdFIgpzdGF0dXMgPSAiQ0FOT05JWkVEIgpkZXNjcmlwdGlvbiA9ICJCcmlkZ2UgYmV0d2VlbiBPcGVuTURXIExpY2Vuc2UgQWdyZWVtZW50IGFuZCBGQ1IgU2ltdWxhdG9yIgo="
        self.work_dir = os.path.dirname(os.path.abspath(__file__))

    def canonize(self):
        bridge_decoded = base64.b64decode(self.bridge_payload).decode("utf-8")
        toml_decoded = base64.b64decode(self.toml_payload).decode("utf-8")

        bridge_path = os.path.join(self.work_dir, "openmdw_fcr_bridge.py")
        with open(bridge_path, "w", encoding="utf-8") as f:
            f.write(bridge_decoded)

        toml_path = os.path.join(self.work_dir, "substrate.toml")
        with open(toml_path, "w", encoding="utf-8") as f:
            f.write(toml_decoded)

        # Dynamic seal
        hasher = hashlib.sha3_256()
        hasher.update(bridge_decoded.encode("utf-8"))
        hasher.update(toml_decoded.encode("utf-8"))
        seal = "sha3-256:" + hasher.hexdigest()

        report = {
            "Substrate": "945",
            "Status": "CANONIZED",
            "Canonical_Seal": seal,
            "Files": [
                "openmdw_fcr_bridge.py",
                "substrate.toml"
            ]
        }

        report_path = os.path.join(self.work_dir, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)

        return report_path

if __name__ == "__main__":
    canonizer = Substrato945OpenMDWFCRBridge()
    output_path = canonizer.canonize()
    print("Substrate 945 canonized at: " + output_path)
