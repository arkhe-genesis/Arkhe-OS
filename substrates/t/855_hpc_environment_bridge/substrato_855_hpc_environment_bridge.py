import json
import base64
import tempfile
import os

class Substrato_855_hpc_environment_bridge:
    def __init__(self):
        self.id = "855-HPC-ENVIRONMENT-BRIDGE"
        script = """#!/ "hpc_bridge_adapter.py" — Substrato 855
import subprocess
import hashlib
import os
from typing import Dict, Optional

class HPCArkheBridge:
    def __init__(self, partition: str = "defq", nodes: int = 1, gpus_per_node: int = 0):
        self.partition = partition
        self.nodes = nodes
        self.gpus = gpus_per_node

    def submit_arkhe_job(self, substrate_id: str, payload_script: str) -> Dict:
        seal = hashlib.sha3_256((str(substrate_id) + ":" + str(payload_script)).encode()).hexdigest()[:16]

        sbatch_script = "#!/bin/bash\n#SBATCH --job-name=ARKHE-" + str(substrate_id) + "\n#SBATCH --partition=" + str(self.partition) + "\n#SBATCH --nodes=" + str(self.nodes) + "\n#SBATCH --gres=gpu:" + str(self.gpus) + "\n#SBATCH --output=/opt/arkhe/logs/%j.out\n\n# ARKHE Metadata\nexport ARKHE_SUBSTRATE_ID=" + str(substrate_id) + "\nexport ARKHE_SEAL=" + str(seal) + "\nexport ARKHE_PHI_C=0.998\n\n# Executar o payload\n" + str(payload_script) + "\n"
        script_path = "/tmp/arkhe_job_" + str(substrate_id) + ".sh"
        with open(script_path, 'w') as f:
            f.write(sbatch_script)

        result = subprocess.run(['sbatch', script_path], capture_output=True, text=True)
        job_id = result.stdout.strip().split()[-1] if result.returncode == 0 else None

        return {
            "job_id": job_id,
            "substrate_id": substrate_id,
            "seal": seal,
            "status": "SUBMITTED" if job_id else "FAILED",
            "decree": "<|ARKHE_START|>\n<|SUBSTRATE|> " + str(substrate_id) + "\n<|JOB_ID|> " + str(job_id) + "\n<|SEAL|> " + str(seal) + "\n<|ARKHE_END|>"
        }

    def check_job_status(self, job_id: str) -> str:
        result = subprocess.run(['sacct', '-j', job_id, '--format=State', '--noheader'],
                                capture_output=True, text=True)
        return result.stdout.strip().split('\n')[0] if result.stdout else "UNKNOWN"

    def run_mpi_kuramoto(self, N: int, K: float, steps: int) -> Dict:
        script = "#!/bin/bash\nmodule load mpi\nmpirun -np " + str(self.nodes) + " python3 -c '\nimport numpy as np\nfrom mpi4py import MPI\ncomm = MPI.COMM_WORLD\nrank = comm.Get_rank()\nsize = comm.Get_size()\nlocal_N = " + str(N) + " // size\ntheta = 2*np.pi*np.random.rand(local_N)\nomega = 2*np.pi*(1+0.1*np.random.randn(local_N))\nfor t in range(" + str(steps) + "):\n    delta = np.subtract.outer(theta, theta)\n    coupling = " + str(K) + "/local_N * np.sum(np.sin(delta), axis=1)\n    theta += 0.01*(omega + coupling)\nr_local = np.abs(np.mean(np.exp(1j*theta)))\nr_global = comm.allreduce(r_local, op=MPI.SUM)/size\nif rank == 0:\n    print(\"Phi_C global = {0:.4f}\".format(r_global))\n'\n"
        return self.submit_arkhe_job("830-TCCE-MPI", script)

if __name__ == "__main__":
    bridge = HPCArkheBridge(partition="gpu", nodes=4, gpus_per_node=2)
    result = bridge.submit_arkhe_job("825-PME-FINETUNE", "python3 train.py --epochs 10")
    print(result["decree"])
"""
        self.b64_adapter = base64.b64encode(script.encode('utf-8')).decode('utf-8')

    def canonize(self):
        seal = "f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1"

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
