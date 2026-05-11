#!/usr/bin/env python3
"""
prepare_calmodulin.py
======================
Preparation script for Calmodulin Dimer GROMACS simulations.
Arkhe(n) Synapse-kappa #14

This script:
1. Downloads PDBs (1CLL for 4Ca, 1CFD for Apo).
2. Creates the intermediate 2Ca state by removing 2 Ca ions from 1CLL.
3. Constructs a dimer system for each state.
4. Runs the GROMACS preparation pipeline (pdb2gmx, editconf, solvate, genion).
5. Prepares 5 replicas for each of the 3 states (15 systems total).

Arkhe-Chain timestamp: 847.621
"""

import os
import subprocess
import urllib.request
import shutil

# Configuration
PDB_URL = "https://files.rcsb.org/download/"
PDBS = {"4ca": "1CLL.pdb", "apo": "1CFD.pdb"}
STATES = ["apo", "2ca", "4ca"]
N_REPLICAS = 5
GMX = "gmx"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUTS_DIR = os.path.join(BASE_DIR, "inputs")
os.makedirs(INPUTS_DIR, exist_ok=True)

def download_pdbs():
    for state, pdb in PDBS.items():
        path = os.path.join(INPUTS_DIR, pdb)
        if not os.path.exists(path):
            print(f"Downloading {pdb}...")
            try:
                urllib.request.urlretrieve(PDB_URL + pdb, path)
            except Exception as e:
                print(f"Failed to download {pdb}: {e}")

def create_2ca_state():
    """Create 2Ca state by removing the last 2 Ca ions from 1CLL.pdb"""
    input_pdb = os.path.join(INPUTS_DIR, "1CLL.pdb")
    output_pdb = os.path.join(INPUTS_DIR, "1CLL_2ca.pdb")

    if not os.path.exists(input_pdb):
        print(f"Input PDB {input_pdb} not found. Skipping 2Ca creation.")
        return

    if os.path.exists(output_pdb):
        return

    print("Creating 2Ca state from 1CLL...")
    with open(input_pdb, 'r') as f:
        lines = f.readlines()

    ca_count = 0
    new_lines = []
    # 1CLL has 4 Calcium ions. We want to keep 2.
    for line in lines:
        if line.startswith("HETATM") and "CA " in line and "CAL" in line:
            ca_count += 1
            if ca_count > 2:
                continue
        new_lines.append(line)

    with open(output_pdb, 'w') as f:
        f.writelines(new_lines)

def run_gmx(cmd):
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running GROMACS: {result.stderr}")
            return False
        return True
    except FileNotFoundError:
        print("GROMACS command 'gmx' not found in path.")
        return False

def prepare_system(state, replica):
    # Parent directory of the script to store system folders
    parent_dir = os.path.dirname(BASE_DIR)
    work_dir = os.path.join(parent_dir, f"{state}_r{replica}")
    os.makedirs(work_dir, exist_ok=True)

    # Select PDB
    if state == "apo":
        src_pdb = os.path.join(INPUTS_DIR, "1CFD.pdb")
    elif state == "4ca":
        src_pdb = os.path.join(INPUTS_DIR, "1CLL.pdb")
    else: # 2ca
        src_pdb = os.path.join(INPUTS_DIR, "1CLL_2ca.pdb")

    if not os.path.exists(src_pdb):
        print(f"Source PDB {src_pdb} not found. Skipping system {state}_r{replica}.")
        return

    # 1. Create Dimer (genconf to double the system)
    dimer_pdb = os.path.join(work_dir, "dimer.pdb")
    subprocess.run([GMX, "genconf", "-f", src_pdb, "-o", dimer_pdb, "-nbox", "2", "1", "1"], capture_output=True)

    # 2. pdb2gmx (AMBER99SB-ILDN and TIP3P)
    run_gmx([GMX, "pdb2gmx", "-f", dimer_pdb, "-o", os.path.join(work_dir, "processed.gro"),
             "-p", os.path.join(work_dir, "topol.top"), "-ff", "amber99sb-ildn", "-water", "tip3p", "-ignh"])

    # 3. editconf (dodecahedron, 1.0 nm)
    run_gmx([GMX, "editconf", "-f", os.path.join(work_dir, "processed.gro"),
             "-o", os.path.join(work_dir, "newbox.gro"), "-c", "-d", "1.0", "-bt", "dodecahedron"])

    # 4. solvate
    run_gmx([GMX, "solvate", "-cp", os.path.join(work_dir, "newbox.gro"),
             "-cs", "spc216.gro", "-o", os.path.join(work_dir, "solvated.gro"),
             "-p", os.path.join(work_dir, "topol.top")])

    # 5. genion (150 mM NaCl)
    # First need a TPR for genion
    run_gmx([GMX, "grompp", "-f", os.path.join(BASE_DIR, "ions.mdp"),
             "-c", os.path.join(work_dir, "solvated.gro"),
             "-p", os.path.join(work_dir, "topol.top"),
             "-o", os.path.join(work_dir, "ions.tpr")])

    # Then run genion
    genion_proc = subprocess.Popen([GMX, "genion", "-s", os.path.join(work_dir, "ions.tpr"),
                                    "-o", os.path.join(work_dir, "solvated_ions.gro"),
                                    "-p", os.path.join(work_dir, "topol.top"),
                                    "-pname", "NA", "-nname", "CL", "-neutral", "-conc", "0.15"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    genion_proc.communicate(input="SOL")

    print(f"System prepared: {state} replica {replica}")

def main():
    print("Arkhe(n) Calmodulin Preparation Start")
    download_pdbs()
    create_2ca_state()

    for state in STATES:
        for r in range(N_REPLICAS):
            print(f"Preparing {state} r{r}...")
            prepare_system(state, r)

    print("Preparation script execution complete.")

if __name__ == "__main__":
    main()
