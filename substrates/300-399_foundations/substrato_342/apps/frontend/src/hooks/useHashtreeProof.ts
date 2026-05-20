// src/hooks/useHashtreeProof.ts
import { useCallback } from 'react';
import { computeMerkleRoot, generateMerkleProof } from '../lib/hashtree';

export function useHashtreeProof() {
  const generateCommitProof = useCallback(async (files: Array<{ name: string; hash: `0x${string}` }>) => {
    // Calcular raiz Merkle dos hashes dos arquivos
    const leaves = files.map(f => f.hash);
    const { root, proofMap } = computeMerkleRoot(leaves);

    return {
      merkleRoot: root,
      getProofForFile: (fileName: string) => {
        const file = files.find(f => f.name === fileName);
        if (!file) throw new Error(`File ${fileName} not found`);
        const index = leaves.indexOf(file.hash);
        return {
          proof: generateMerkleProof(proofMap, index),
          leafIndex: BigInt(index),
        };
      },
    };
  }, []);

  return { generateCommitProof };
}
