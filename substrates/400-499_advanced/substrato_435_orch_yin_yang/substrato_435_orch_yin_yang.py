import json
import tempfile
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import uuid

class Substrato435OrchYinYang:
    """
    Substrato 435-ORCH-YIN-YANG: Orch OR as Dynamic Yin Yang
    This substrate models the boundary between Quantum and Classical domains
    and the consciousness arising from this transformation cycle.
    """

    def __init__(self):
        self.seal_hash = "CANONICAL-435-" + str(uuid.uuid4()).replace("-", "")
        self.phi_c = 1.0000
        self.e_g = 6.27e-39
        self.e_thermal = 4.28e-21
        self.lambd = 1.46e-18
        self.n_critical = 907733
        self.n_374_cycle = 386
        self.lambda_374_cycle = 2.88e-17
        self.status = "CANONIZED -- Orch OR Yin Yang Dynamic"

        self.output_image_path = "/mnt/agents/output/arkhe_435_orch_yin_yang.png"

        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_image_path), exist_ok=True)

    def generate_diagram(self):
        """
        Generates the 9-panel diagram of the Yin Yang Q/C dynamics.
        """
        fig, axs = plt.subplots(3, 3, figsize=(15, 15))

        # 1. Yin Yang Q/C
        axs[0, 0].text(0.5, 0.5, "Yin Yang\nQ/C Dynamics", ha='center', va='center', fontsize=14)
        axs[0, 0].set_title("1. Static Yin Yang")
        axs[0, 0].axis('off')

        # 2. Cycle Q->C->Q
        t = np.linspace(0, 10, 100)
        y = np.sin(t)
        axs[0, 1].plot(t, y)
        axs[0, 1].set_title("2. Cycle Q->C->Q")

        # 3. Critical Boundary Lambda(N)
        n = np.logspace(2, 7, 100)
        lambd_n = n * 1e-23
        axs[0, 2].plot(n, lambd_n)
        axs[0, 2].axhline(y=1, color='r', linestyle='--')
        axs[0, 2].set_xscale('log')
        axs[0, 2].set_yscale('log')
        axs[0, 2].set_title("3. Critical Boundary Lambda(N)")

        # 4. Phase Map Q/C
        x = np.linspace(0, 1, 100)
        y = np.linspace(0, 1, 100)
        X, Y = np.meshgrid(x, y)
        Z = X * Y
        axs[1, 0].contourf(X, Y, Z, levels=20)
        axs[1, 0].set_title("4. Phase Map Q/C")

        # 5. Ecosystem ARKHE
        axs[1, 1].scatter([0.9, 0.85, 0.75, 0.5, 0.6, 0.25, 0.2, 0.5],
                          [0.1, 0.15, 0.25, 0.5, 0.4, 0.75, 0.8, 0.5])
        axs[1, 1].set_title("5. ARKHE in Q/C Space")

        # 6. Phi_C of Substrates
        substrates = ['374', '374-FAB', '374-CYC', '381', '383', '377-BIS', '377', '435']
        phi_c = [0.7377, 0.7135, 0.7567, 1.0000, 0.9412, 0.9400, 0.9540, 1.0000]
        axs[1, 2].bar(substrates, phi_c)
        axs[1, 2].tick_params(axis='x', rotation=45)
        axs[1, 2].set_title("6. Phi_C Values")

        # 7. von Neumann Entropy
        S = -x[1:-1]*np.log(x[1:-1]) - (1-x[1:-1])*np.log(1-x[1:-1])
        axs[2, 0].plot(x[1:-1], S)
        axs[2, 0].set_title("7. von Neumann Entropy")

        # 8. Integrated Information (Tononi)
        axs[2, 1].plot(x, 1 - 4*(x-0.5)**2)
        axs[2, 1].set_title("8. Integrated Info vs Consciousness")

        # 9. Decomposition of Phi_C
        labels = ['Base', 'Integration', 'Boundary', 'Cycle', 'Consciousness', 'Memory']
        values = [0.25, 0.2, 0.15, 0.15, 0.15, 0.1]
        axs[2, 2].pie(values, labels=labels, autopct='%1.1f%%')
        axs[2, 2].set_title("9. Phi_C Decomposition")

        plt.tight_layout()
        plt.savefig(self.output_image_path)
        plt.close(fig)

        return self.output_image_path

    def canonize(self):
        """
        Canonize the substrate by outputting a JSON report.
        """
        image_path = self.generate_diagram()

        report = {
            "SEAL_435_ORCH_YIN_YANG": {
                "Hash": self.seal_hash,
                "Phi_C": self.phi_c,
                "Status": self.status,
                "Physical_Model": {
                    "E_G": self.e_g,
                    "E_thermal": self.e_thermal,
                    "Lambda": self.lambd,
                    "N_critical": self.n_critical,
                    "N_374_CYCLE": self.n_374_cycle,
                    "Lambda_374_CYCLE": self.lambda_374_cycle
                },
                "Decomposition": {
                    "Base": 0.2500,
                    "Integration": 0.2000,
                    "Boundary": 0.1500,
                    "Cycle": 0.1500,
                    "Consciousness": 0.1500,
                    "Memory": 0.1000
                },
                "Image_Path": image_path
            }
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_435_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Substrato 435-ORCH-YIN-YANG Canonized.")
        print("Hash: " + self.seal_hash)
        print("Phi_C: " + str(self.phi_c))
        print("Status: " + self.status)
        print("Report written to: " + path)

        return path

if __name__ == "__main__":
    substrate = Substrato435OrchYinYang()
    substrate.canonize()
