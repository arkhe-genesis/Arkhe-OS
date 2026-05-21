import solcx
import os
import sys

# Change default solc installation path to bypass permission issues or path conflicts
solcx.import_installed_solc()
if '0.8.28' not in solcx.get_installed_solc_versions():
    solcx.install_solc('0.8.28')

solcx.set_solc_version('0.8.28')

import_remappings = []
if os.path.exists("node_modules"):
    import_remappings.append("@openzeppelin=node_modules/@openzeppelin")

from solcx import compile_files
try:
    compile_files(['substrates/300-399_foundations/substrato_372/contracts/HumanityProof.sol', 'substrates/300-399_foundations/substrato_372/contracts/ZKInferenceVerifier.sol', 'substrates/300-399_foundations/substrato_372/contracts/TuringTestDAO.sol'], output_values=['abi', 'bin'], import_remappings=import_remappings)
    print("Compilation successful")
except Exception as e:
    print(f"Compilation failed: {e}")
