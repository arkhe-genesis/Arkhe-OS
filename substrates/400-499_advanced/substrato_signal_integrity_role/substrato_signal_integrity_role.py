import json
import tempfile
import os

class SubstratoSignalIntegrityRole:
    def canonize(self):
        report = {
            "Title": "Signal Integrity Engineer",
            "Role": "You are a Signal Integrity Engineer joining in our hardware team and help ensure our AI-powered devices perform flawlessly at the electrical level. In this role, you'll own SI analysis across high-speed interfaces - DDR, PCIe, USB, MIPI - and work closely with our PCB layout, ASIC, and mechanical design teams to solve the unique challenges that come with packing serious compute into compact, thermally constrained form factors. You'll run simulations, validate designs in the lab, and feed findings back into our design rules as we scale from prototypes to volume production.",
            "Responsibilities": {
                "SI Analysis": "Perform pre-layout and post-layout signal integrity simulations for high-speed interfaces (DDR4/5, PCIe Gen3/4, USB 3.x, MIPI CSI/DSI).",
                "PI Analysis": "Model and optimize power distribution networks (PDN), including decoupling strategies, plane resonance, and target impedance.",
                "Channel Modeling": "Build channel models for SerDes links, run eye diagram analysis, and validate compliance margins.",
                "PCB Stackup": "Define PCB stackup, impedance profiles, and routing constraints in collaboration with layout engineers.",
                "Lab Validation": "Conduct bench-level measurements using oscilloscopes, VNAs, TDR, and spectrum analyzers to correlate simulation with hardware.",
                "EMI/EMC": "Identify and mitigate electromagnetic interference issues at the board and system level, supporting regulatory certification.",
                "Design Rules": "Develop and maintain SI/PI design guidelines and constraint sets for the hardware team."
            },
            "Requirements": {
                "Education": "BS/MS in Electrical Engineering with a focus on electromagnetics, RF, or signal integrity.",
                "Tool Proficiency": "Hands-on experience with SI/PI tools such as Ansys HFSS, Keysight ADS/PathWave, Cadence Sigrity, or Simbeor.",
                "High-Speed Interfaces": "Deep working knowledge of DDR, PCIe, USB, and/or MIPI signaling standards and compliance testing.",
                "Lab Skills": "Expert-level skills with high-bandwidth oscilloscopes, VNAs, TDR equipment, and near-field EMI probes.",
                "PCB Knowledge": "Strong understanding of multi-layer PCB fabrication, materials (Dk/Df), and controlled-impedance routing."
            },
            "Bonus Qualifications": [
                "Experience with LPDDR5 or high-speed memory interfaces on mobile/edge compute platforms.",
                "Background in RFIC or antenna design for Wi-Fi, Bluetooth, or UWB systems.",
                "Familiarity with 3D electromagnetic solvers for package-level or connector modeling.",
                "Experience supporting EMC certification (FCC, CE, VCCI) from design through test."
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_si_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Signal Integrity Engineer Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoSignalIntegrityRole()
    substrate.canonize()
