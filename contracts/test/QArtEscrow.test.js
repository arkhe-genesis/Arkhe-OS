const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("ARKHE Royalty Escrow", function () {
  let escrow;
  let owner, depositor, beneficiary, resolver;
  let depositId;
  const RELEASE_DELAY = 86400; // 1 dia
  const EXPIRY_DELAY = 604800; // 7 dias
  const DEPOSIT_AMOUNT = ethers.parseEther("1.0");

  beforeEach(async function () {
    [owner, depositor, beneficiary, resolver] = await ethers.getSigners();

    const Escrow = await ethers.getContractFactory("ARKHERoyaltyEscrow");
    escrow = await Escrow.deploy({
      defaultReleaseDelay: RELEASE_DELAY,
      defaultExpiryDelay: EXPIRY_DELAY,
      minDeposit: ethers.parseEther("0.01"),
      maxDeposit: ethers.parseEther("1000"),
      protocolTreasury: owner.address,
      disputeResolver: resolver.address,
    });
    await escrow.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set correct initial config", async function () {
      expect(await escrow.defaultReleaseDelay()).to.equal(RELEASE_DELAY);
      expect(await escrow.defaultExpiryDelay()).to.equal(EXPIRY_DELAY);
      expect(await escrow.minDeposit()).to.equal(ethers.parseEther("0.01"));
      expect(await escrow.disputeResolver()).to.equal(resolver.address);
    });
  });

  describe("Deposit", function () {
    it("Should create a deposit", async function () {
      const tx = await depositor.sendTransaction({
        to: escrow.target,
        value: DEPOSIT_AMOUNT,
        data: "0x", // fallback
      });

      // Criar depósito via função
      const createTx = await escrow
        .connect(depositor)
        .createDeposit(beneficiary.address, ethers.ZeroAddress, 0, {
          value: DEPOSIT_AMOUNT,
        });

      const receipt = await createTx.wait();
      const event = receipt.logs.find(
        (l) => l.fragment && l.fragment.name === "DepositCreated"
      );

      expect(event).to.exist;
      depositId = event.args.depositId;

      const deposit = await escrow.deposits(depositId);
      expect(deposit.depositor).to.equal(depositor.address);
      expect(deposit.beneficiary).to.equal(beneficiary.address);
      expect(deposit.amount).to.equal(DEPOSIT_AMOUNT);
    });

    it("Should reject deposit below minimum", async function () {
      await expect(
        escrow
          .connect(depositor)
          .createDeposit(beneficiary.address, ethers.ZeroAddress, 0, {
            value: ethers.parseEther("0.001"),
          })
      ).to.be.revertedWith("Escrow: below minimum deposit");
    });
  });
});
