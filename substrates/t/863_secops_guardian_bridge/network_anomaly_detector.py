#!/ "network_anomaly_detector.py"
import subprocess
import re

class NetworkAnomalyDetector:
    def __init__(self):
        self.known_malicious_ips = set()

    def scan_connections(self):
        output = subprocess.check_output(["netstat", "-ntup"]).decode()
        for line in output.splitlines():
            if "ESTABLISHED" in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+):\d+\s+ESTABLISHED', line)
                if match:
                    ip = match.group(1)
                    if ip in self.known_malicious_ips:
                        print("[ALERTA] Conexão com IP malicioso: " + ip)
                        subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"])
