with open('substrate-6070/src/lib.rs') as f:
    text = f.read()

index = text.find('    pub fn verify(\n        proof: plonky2::plonk::proof::ProofWithPublicInputs<F, C, D>,')

if index != -1:
    end_index = text.find('}', index)
    end_index = text.find('}', end_index + 1)
    text = text[:end_index+1] + '\n}\n' + text[end_index+1:]

    with open('substrate-6070/src/lib.rs', 'w') as f:
        f.write(text)
