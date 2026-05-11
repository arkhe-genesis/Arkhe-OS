import { expect } from "chai";
import { ethers } from "hardhat";

describe("ARKHERoyaltyEscrow", function () {
  it("Should create a deposit", async function () {
    const [owner, disputeResolver, beneficiary] = await ethers.getSigners();

    const Escrow = await ethers.getContractFactory("ARKHERoyaltyEscrow");
    const config = {
      defaultReleaseDelay: 86400,
      defaultExpiryDelay: 86400 * 2,
      minDeposit: 100,
      maxDeposit: ethers.parseEther("1000"),
      disputeResolver: disputeResolver.address,
      protocolTreasury: owner.address
    };

    const escrow = await Escrow.deploy(config);

    await expect(
      escrow.createDeposit(beneficiary.address, ethers.ZeroAddress, 0, { value: 1000 })
    ).to.emit(escrow, "DepositCreated");
  });
});
