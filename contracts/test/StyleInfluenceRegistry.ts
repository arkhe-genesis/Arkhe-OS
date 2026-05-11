import { expect } from "chai";
import { ethers } from "hardhat";

describe("StyleInfluenceRegistry", function () {
  it("Should register a fingerprint", async function () {
    const StyleInfluenceRegistry = await ethers.getContractFactory("StyleInfluenceRegistry");
    const registry = await StyleInfluenceRegistry.deploy(32768);

    const perceptualHash = ethers.zeroPadValue("0x1234", 32);
    const styleHash = ethers.zeroPadValue("0x5678", 32);

    await expect(registry.registerFingerprint(perceptualHash, styleHash, "ipfs://uri"))
      .to.emit(registry, "FingerprintRegistered");
  });
});
