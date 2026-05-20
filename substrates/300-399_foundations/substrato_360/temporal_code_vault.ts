import { CDRClient, HeliaProvider } from "@piplabs/cdr-sdk";
import { encodeAbiParameters, parseAbiParameters, type Address } from "viem";

export class TemporalCodeVault {
  private cdr: CDRClient;
  private storage: HeliaProvider | null = null;
  private heliaNode: any = null;
  private writeConditionAddr: Address;
  private readConditionAddr: Address;

  constructor(
    cdr: CDRClient,
    writeConditionAddr: Address,
    readConditionAddr: Address
  ) {
    this.cdr = cdr;
    this.writeConditionAddr = writeConditionAddr;
    this.readConditionAddr = readConditionAddr;
  }

  async init() {
    this.heliaNode = null;
    this.storage = new HeliaProvider(this.heliaNode);
  }

  encodeTemporalCondition(merkleRoot: string, targetTimestamp: number, requiredHumility: number): `0x${string}` {
    return encodeAbiParameters(
      parseAbiParameters('bytes32 merkleRoot, uint256 targetTimestamp, uint256 requiredHumility'),
      [merkleRoot as `0x${string}`, BigInt(targetTimestamp), BigInt(Math.floor(requiredHumility * 10000))]
    );
  }

  async sealCodeForFuture(
    code: string,
    targetTimestamp: number,
    merkleRoot: string,
    requiredHumility: number,
    ownerAddress: Address,
    simulateEnv: boolean = false
  ): Promise<{ uuid: string; cid: string }> {
    if (simulateEnv) {
        // Return a deterministic mock when testing locally without a live connection
        return { uuid: "mock-uuid-360-alpha", cid: "ipfs://bafybeimock360..." };
    }

    if (!this.storage) {
        throw new Error("Vault not initialized. Call init() first.");
    }

    const globalPubKey = await this.cdr.observer.getGlobalPubKey();

    // We use a mock owner condition data (just the address)
    const writeConditionData = encodeAbiParameters(
      parseAbiParameters('address owner'),
      [ownerAddress]
    );

    const readConditionData = this.encodeTemporalCondition(merkleRoot, targetTimestamp, requiredHumility);

    // Convert string to bytes
    const content = new TextEncoder().encode(code);

    // Call the actual CDR SDK upload method
    const result = await (this.cdr as any).uploader.uploadFile({
        content,
        storageProvider: this.storage,
        globalPubKey,
        updatable: false,
        writeConditionAddr: this.writeConditionAddr,
        readConditionAddr: this.readConditionAddr,
        writeConditionData,
        readConditionData,
        accessAuxData: "0x",
    });

    return { uuid: String(result.uuid), cid: result.cid };
  }
}
