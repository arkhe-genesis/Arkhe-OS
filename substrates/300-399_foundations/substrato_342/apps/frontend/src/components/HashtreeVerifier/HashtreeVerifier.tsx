// src/components/HashtreeVerifier/HashtreeVerifier.tsx
import { useState } from 'react';
import { useContractRead } from 'wagmi';
import { computeMerkleRoot, verifyMerkleProof } from '../../lib/hashtree';
import { ABI as COMMIT_REGISTRY_ABI } from '../../contracts/CodeCommitRegistryHashtree';

interface HashtreeVerifierProps {
  commitId: string;
  fileName: string;
  fileHash: `0x${string}`;
}

export function HashtreeVerifier({ commitId, fileName, fileHash }: HashtreeVerifierProps) {
  const [proof, setProof] = useState<`0x${string}`[]>([]);
  const [leafIndex, setLeafIndex] = useState<bigint>(0n);
  const [verified, setVerified] = useState<boolean | null>(null);

  // Ler merkleRoot do contrato
  const [authorTokenId, commitNonce] = commitId.split('-');
  const { data: merkleRoot } = useContractRead({
    address: process.env.NEXT_PUBLIC_COMMIT_REGISTRY,
    abi: COMMIT_REGISTRY_ABI,
    functionName: 'getCommitMerkleRoot',
    args: [authorTokenId, commitNonce],
  });

  const handleVerify = async () => {
    if (!merkleRoot || proof.length === 0) return;

    const isValid = verifyMerkleProof({
      root: merkleRoot,
      proof,
      leaf: fileHash,
      index: leafIndex,
    });

    setVerified(isValid);
  };

  const handleUploadProof = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    file.text().then(content => {
      const { proof: p, index } = JSON.parse(content);
      setProof(p);
      setLeafIndex(BigInt(index));
    });
  };

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <h3 className="font-semibold mb-2">Verificar Integridade do Arquivo</h3>
      <p className="text-sm text-gray-600 mb-4">
        Arquivo: <code>{fileName}</code><br />
        Hash: <code>{fileHash.slice(0, 16)}...</code>
      </p>

      <input
        type="file"
        accept=".json"
        onChange={handleUploadProof}
        className="mb-4"
      />

      <button
        onClick={handleVerify}
        disabled={!merkleRoot || proof.length === 0}
        className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
      >
        Verificar Prova Merkle
      </button>

      {verified !== null && (
        <div className={`mt-4 p-3 rounded ${verified ? 'bg-green-100' : 'bg-red-100'}`}>
          {verified ? '✅ Arquivo verificado — pertence ao commit' : '❌ Verificação falhou — arquivo pode ter sido adulterado'}
        </div>
      )}
    </div>
  );
}
