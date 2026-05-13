with open('substrate-6070/src/lib.rs') as f:
    text = f.read()

index = text.find('// ─────────────────────────────────────────────────────────────\n// 5. ZK CIRCUIT SKELETON (Plonky2)')

if index != -1:
    end_index = text.find('/// Shannon entropy of a byte stream.', index)
    if end_index != -1:
        text = text[:index] + text[end_index:]

    with open('substrate-6070/src/lib.rs', 'w') as f:
        f.write(text)
