with open('substrate-6070/src/lib.rs') as f:
    text = f.read()

text = text.replace('    pub fn verify(\n        proof: plonky2::plonk::proof::ProofWithPublicInputs<F, C, D>,\n        verifier_data: plonky2::plonk::circuit_data::VerifierCircuitData<F, C, D>,\n    ) -> anyhow::Result<()> {\n        verifier_data.verify(proof)\n    }\n/// Shannon entropy of a byte stream.', '    pub fn verify(\n        proof: plonky2::plonk::proof::ProofWithPublicInputs<F, C, D>,\n        verifier_data: plonky2::plonk::circuit_data::VerifierCircuitData<F, C, D>,\n    ) -> anyhow::Result<()> {\n        verifier_data.verify(proof)\n    }\n}\n/// Shannon entropy of a byte stream.')

with open('substrate-6070/src/lib.rs', 'w') as f:
    f.write(text)
