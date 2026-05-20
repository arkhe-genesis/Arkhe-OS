import { createPublicClient, createWalletClient, http, type Address, getContract, keccak256, encodeAbiParameters, encodePacked } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { foundry } from "viem/chains";
import { ArkheCDRBridge } from "./arkhe_cdr_bridge.js";
import { TemporalCodeVault } from "./temporal_code_vault.js";
import { SGXAttestationValidator } from "./sgx_attestation.js";

// Dummy ABI for TemporalMerkleCondition purely for simulation interactions
const conditionAbi = [
  {
    "inputs": [
      { "internalType": "uint256", "name": "timestamp", "type": "uint256" },
      { "internalType": "bytes32", "name": "merkleRoot", "type": "bytes32" }
    ],
    "name": "finalizeBlock",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "user", "type": "address" },
      { "internalType": "uint256", "name": "score", "type": "uint256" }
    ],
    "name": "setUserHumility",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
] as const;

async function runSimulation() {
  console.log("=== SUBSTRATO 360: TEMPORAL VAULT CYCLE SIMULATION ===");

  const GHOST_THRESHOLD = 0.5774;

  // 1. Setup Anvil Clients
  const account = privateKeyToAccount("0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80");
  const publicClient = createPublicClient({ chain: foundry, transport: http() });
  const walletClient = createWalletClient({ account, chain: foundry, transport: http() });

  // Address deployed via the Forge Script earlier
  const conditionAddress: Address = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const ownerWriteConditionAddr: Address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"; // mock

  // Construct a valid Merkle Root for the simulation since the contract now requires it
  const vaultAddress: Address = conditionAddress; // For simplicity in sim
  const innerHash1 = keccak256(encodeAbiParameters([{ type: 'address' }, { type: 'address' }], [account.address, vaultAddress]));
  const leaf1 = keccak256(encodePacked(['bytes'], [innerHash1]));

  const dummyUser: Address = "0x0000000000000000000000000000000000000004";
  const innerHash2 = keccak256(encodeAbiParameters([{ type: 'address' }, { type: 'address' }], [dummyUser, vaultAddress]));
  const leaf2 = keccak256(encodePacked(['bytes'], [innerHash2]));

  let mockMerkleRoot: `0x${string}`;
  if (BigInt(leaf1) <= BigInt(leaf2)) {
    mockMerkleRoot = keccak256(encodePacked(['bytes32', 'bytes32'], [leaf1, leaf2]));
  } else {
    mockMerkleRoot = keccak256(encodePacked(['bytes32', 'bytes32'], [leaf2, leaf1]));
  }

  // 2. Instantiate ArkheBridge & Vault
  console.log("Instantiating ArkheCDRBridge...");
  const bridge = new ArkheCDRBridge(walletClient as any, publicClient as any);

  console.log("Instantiating TemporalCodeVault...");
  const vault = new TemporalCodeVault(bridge.cdr, ownerWriteConditionAddr, conditionAddress);

  // We mock the init and sealing process to avoid heavy IPFS/WASM dependencies failing in quick sim
  console.log("Simulating Vault initialization & connection...");

  // 3. Payload & Humility Check
  const payload = "function extractPhiC() { return 0.618; } // Canonical code";
  console.log("Measuring Humility of payload...");
  const humility = bridge.measureHumility(payload);
  console.log(`Humility Score: ${humility}`);
  if (humility < GHOST_THRESHOLD) {
     throw new Error("Payload rejected: Humility below GHOST threshold.");
  }

  // 4. Seal Code
  const targetTimestamp = Math.floor(Date.now() / 1000) + 10;
  console.log(`Sealing code for timestamp >= ${targetTimestamp} with merkle root ${mockMerkleRoot}...`);

  // We intercept the CDR upload in simulation and assert variables
  const readConditionData = vault.encodeTemporalCondition(mockMerkleRoot, targetTimestamp, humility);
  console.log("Encoded Read Condition Data:", readConditionData);

  const sealed = await vault.sealCodeForFuture(payload, targetTimestamp, mockMerkleRoot, humility, account.address, true);
  console.log("Sealed successfully. UUID:", sealed.uuid, "CID:", sealed.cid);

  // 5. Simulate future event on-chain
  console.log("Simulating Temporal Block Finalization on-chain...");
  const conditionContract = getContract({
      address: conditionAddress,
      abi: conditionAbi,
      client: { public: publicClient, wallet: walletClient }
  });

  const tx = await conditionContract.write.finalizeBlock([BigInt(targetTimestamp), mockMerkleRoot]);
  const receipt = await publicClient.waitForTransactionReceipt({ hash: tx });
  console.log("Block finalized. TxHash:", receipt.transactionHash);

  // 6. Test SGX Attestation
  console.log("Validating SGX Attestation of Time-Weaver Node...");
  const validator = new SGXAttestationValidator();
  // Using a mock string as parsing actual quotes requires real hardware signatures
  const mockAttestation = "0x0000000000000000000000000000000000000000000000000000000000000000";
  // We expect this to fail now since it's an invalid quote from which mrenclave cannot be extracted
  await validator.validateEnclave(mockAttestation);

  console.log("=== CYCLE COMPLETE: REVELATION CONDITIONS MET ===");
}

runSimulation().catch(console.error);
