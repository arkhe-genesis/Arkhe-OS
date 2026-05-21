import numpy as np
import matplotlib.pyplot as plt
import json
import tempfile
import os
import matplotlib
matplotlib.use('Agg')


class Substrato430BlueMobile:
    """
    Substrato 430-BLUE-MOBILE: First truly mobile quantum processor of ARKHE OS
    Integrating 9 substrates (418->429) in a unified SoC architecture.
    Physical footprint: 5x5 mm^2, 18 physical qubits, 115 mW, 10 mK.
    """

    def __init__(self):
        self.seal_hash = \
            "8043d33a4d66b03a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4"
        self.phi_c = 0.8007
        self.status = "CANONIZADO"

        self.specs = {
            "dimensions": "5.0 x 5.0 mm2",
            "cores": 6,
            "core_type": "Josephson rings (418-PROTO)",
            "qubits_physical": 18,
            "qubits_logical": 2,
            "correction_code": "Hexagonal d=17, t=8",
            "native_gates": [
                "Single-qubit",
                "CNOT (425)",
                "Toffoli (428-CLIQUE)"]}

        self.pipeline = [
            {"stage": "Initialization", "time_ns": 10, "fidelity": 0.990},
            {"stage": "Single-qubit", "time_ns": 1, "fidelity": 0.999},
            {"stage": "CNOT", "time_ns": 5, "fidelity": 0.995},
            {"stage": "Toffoli", "time_ns": 20, "fidelity": 0.980},
            {"stage": "Error Correction", "time_ns": 200, "fidelity": 0.950},
            {"stage": "SQUID Readout", "time_ns": 50, "fidelity": 0.990}
        ]

        self.energy = [
            {"subsystem": "Qubits (18)", "power_mw": 0.000018},
            {"subsystem": "CMOS Control", "power_mw": 10.0},
            {"subsystem": "SQUID Readout", "power_mw": 5.0},
            {"subsystem": "Dilution Fridge", "power_mw": 100.0}
        ]

        self.connectivity = [
            {"layer": "Native eSIM (405)", "fidelity": 0.999},
            {"layer": "WiFi-CSI (389/406)", "fidelity": 0.975},
            {"layer": "AGI-MCP (381)", "fidelity": 0.990},
            {"layer": "HyperCycle (362)", "fidelity": 0.999}
        ]

        self.benchmarks = [{"system": "IBM Condor",
                            "qubits": 1121,
                            "fid_2q": 0.995,
                            "t_coh_ms": 0.1,
                            "vol_cm3": 1000.0},
                           {"system": "Google Sycamore",
                            "qubits": 70,
                            "fid_2q": 0.996,
                            "t_coh_ms": 0.02,
                            "vol_cm3": 500.0},
                           {"system": "IonQ Forte",
                            "qubits": 36,
                            "fid_2q": 0.998,
                            "t_coh_ms": 10.0,
                            "vol_cm3": 2000.0},
                           {"system": "ARKHE 430",
                            "qubits": 18,
                            "fid_2q": 0.995,
                            "t_coh_ms": 0.2,
                            "vol_cm3": 0.001}]

        self.phi_c_decomposition = {
            "Base": {"weight": 0.25, "value": 0.2500},
            "Integration": {"weight": 0.20, "value": 0.2000},
            "Fidelity": {"weight": 0.20, "value": 0.1814},
            "Robustness": {"weight": 0.15, "value": 0.0680},
            "Mobility": {"weight": 0.15, "value": 0.0810},
            "Efficiency": {"weight": 0.15, "value": 0.0203}
        }

    def generate_artifact(self):
        """
        Generates the arkhe_430_blue_mobile.png artifact with 6 panels.
        """
        # Set up a 2x3 grid of subplots
        fig, axs = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(
            "ARKHE OS - Substrato 430-BLUE-MOBILE Canonization",
            fontsize=20,
            fontweight='bold')

        # Panel 1: Chip Layout
        ax = axs[0, 0]
        ax.set_title("Layout do Chip (Top View)")
        ax.axis('off')

        # Draw the 5x5mm chip boundary
        chip = plt.Rectangle((0, 0), 5, 5, fill=False,
                             edgecolor='black', linewidth=2)
        ax.add_patch(chip)

        # Hexagonal arrangement of 6 cores + central SQUID
        angles = np.linspace(0, 2 * np.pi, 6, endpoint=False)
        r = 1.5
        center = (2.5, 2.5)

        # Central SQUID
        squid = plt.Circle(center, 0.4, color='red', alpha=0.5, label='SQUID')
        ax.add_patch(squid)

        # Cores
        for i, angle in enumerate(angles):
            x = center[0] + r * np.cos(angle)
            y = center[1] + r * np.sin(angle)
            core = plt.Circle((x, y), 0.5, color='blue', alpha=0.5)
            ax.add_patch(core)
            # Add 3 qubits per core
            for j in range(3):
                qx = x + 0.2 * np.cos(j * 2 * np.pi / 3)
                qy = y + 0.2 * np.sin(j * 2 * np.pi / 3)
                qubit = plt.Circle((qx, qy), 0.08, color='gold')
                ax.add_patch(qubit)

        ax.set_xlim(-0.5, 5.5)
        ax.set_ylim(-0.5, 5.5)
        ax.text(2.5, -0.2, "5.0 x 5.0 mm²", ha='center')

        # Panel 2: Temporal Pipeline
        ax = axs[0, 1]
        ax.set_title("Pipeline de Execucao (Tempo vs Fidelidade)")
        stages = [s["stage"] for s in self.pipeline]
        times = [s["time_ns"] for s in self.pipeline]
        fidelities = [s["fidelity"] for s in self.pipeline]

        x = np.arange(len(stages))
        ax.bar(x, times, color='lightblue', label='Tempo (ns)')
        ax.set_ylabel('Tempo (ns)')
        ax.set_xticks(x)
        ax.set_xticklabels(stages, rotation=45, ha='right')

        ax2 = ax.twinx()
        ax2.plot(
            x,
            fidelities,
            color='darkgreen',
            marker='o',
            linewidth=2,
            label='Fidelidade')
        ax2.set_ylabel('Fidelidade')
        ax2.set_ylim(0.9, 1.01)

        # Panel 3: Benchmark Comparativo (Volume)
        ax = axs[0, 2]
        ax.set_title("Benchmark: Volume Fisico (cm³)")
        systems = [b["system"] for b in self.benchmarks]
        volumes = [b["vol_cm3"] for b in self.benchmarks]

        ax.barh(systems, volumes, color=['gray', 'gray', 'gray', 'blue'])
        ax.set_xscale('log')
        ax.set_xlabel('Volume (cm³) - Escala Log')
        ax.invert_yaxis()  # Labels read top-to-bottom

        # Panel 4: Hierarquia Termica Log
        ax = axs[1, 0]
        ax.set_title("Hierarquia Termica (K)")
        levels = ["Ambiente", "He-4", "He-3/He-4 (Diluicao)"]
        temps = [300.0, 4.0, 0.01]  # 10mK = 0.01K

        ax.plot(
            levels,
            temps,
            marker='s',
            markersize=10,
            linestyle='-',
            linewidth=2,
            color='orange')
        ax.set_yscale('log')
        ax.set_ylabel('Temperatura (K) - Escala Log')
        for i, txt in enumerate(temps):
            ax.annotate(
                f"{txt} K",
                (levels[i],
                 temps[i]),
                textcoords="offset points",
                xytext=(
                    0,
                    10),
                ha='center')

        # Panel 5: Consumo Energetico Log
        ax = axs[1, 1]
        ax.set_title("Consumo Energetico (mW)")
        subs = [e["subsystem"] for e in self.energy]
        powers = [e["power_mw"] for e in self.energy]

        ax.bar(subs, powers, color='purple')
        ax.set_yscale('log')
        ax.set_ylabel('Potencia (mW) - Escala Log')
        ax.set_xticks(np.arange(len(subs)))
        ax.set_xticklabels(subs, rotation=45, ha='right')

        # Panel 6: Decomposicao do Phi_C
        ax = axs[1, 2]
        ax.set_title(f"Decomposicao do Phi_C = {self.phi_c}")
        labels = list(self.phi_c_decomposition.keys())
        values = [d["value"] for d in self.phi_c_decomposition.values()]

        # Explode the 'Integration' wedge slightly
        explode = [0] * len(labels)
        explode[1] = 0.1

        ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            explode=explode,
            colors=plt.cm.Paired(
                np.linspace(
                    0,
                    1,
                    len(labels))))
        # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.axis('equal')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        # Save to temporary file securely
        output_dir = "/tmp"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        fd, path = tempfile.mkstemp(dir=output_dir,
            suffix=".png", prefix="arkhe_430_blue_mobile_")
        os.close(fd)  # Close file descriptor since savefig opens it
        plt.savefig(path)
        plt.close(fig)
        return path

    def canonize(self):
        """
        Outputs canonical report to JSON securely and generates artifact.
        """
        img_path = self.generate_artifact()

        report = {
            "Substrate": "430-BLUE-MOBILE",
            "Phi_C": self.phi_c,
            "Seal": self.seal_hash,
            "Status": self.status,
            "Artifact": img_path,
            "Specs": self.specs,
            "Total_Pipeline_Time_ns": sum(s["time_ns"] for s in self.pipeline),
            "Total_Power_mW": sum(e["power_mw"] for e in self.energy)
        }

        output_dir = "/tmp"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        fd, path = tempfile.mkstemp(dir=output_dir, suffix=".json", prefix="substrate_430_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        return path, img_path


if __name__ == "__main__":
    substrate = Substrato430BlueMobile()
    json_path, img_path = substrate.canonize()
    print("Canonizacao Concluida.")
    print("Relatorio:", json_path)
    print("Artefato:", img_path)
