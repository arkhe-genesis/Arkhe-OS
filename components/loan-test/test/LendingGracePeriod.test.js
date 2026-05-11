import { expect } from "chai";
import pkg from "hardhat";
const { ethers, network } = pkg;

describe("Lending Grace Period Test", function () {
  let corn, cornDEX, lending, movePrice;
  let owner, user, liquidator;
  const INITIAL_LIQUIDITY_ETH = ethers.parseEther("100");
  const INITIAL_LIQUIDITY_CORN = ethers.parseEther("100"); // 1:1 price
  const DEPOSIT_AMOUNT = ethers.parseEther("10");

  beforeEach(async function () {
    [owner, user, liquidator] = await ethers.getSigners();

    const Corn = await ethers.getContractFactory("Corn");
    corn = await Corn.deploy();

    const CornDEX = await ethers.getContractFactory("CornDEX");
    cornDEX = await CornDEX.deploy(await corn.getAddress());

    const Lending = await ethers.getContractFactory("Lending");
    lending = await Lending.deploy(await cornDEX.getAddress(), await corn.getAddress());

    const MovePrice = await ethers.getContractFactory("MovePrice");
    movePrice = await MovePrice.deploy(await cornDEX.getAddress(), await corn.getAddress());

    // Setup initial liquidity
    await corn.mintTo(owner.address, INITIAL_LIQUIDITY_CORN);
    await corn.approve(await cornDEX.getAddress(), INITIAL_LIQUIDITY_CORN);
    await cornDEX.init(INITIAL_LIQUIDITY_CORN, { value: INITIAL_LIQUIDITY_ETH });

    // Mint some CORN to Lending contract for users to borrow
    await corn.mintTo(await lending.getAddress(), ethers.parseEther("1000"));

    // Prepare liquidator with some CORN
    await corn.mintTo(liquidator.address, ethers.parseEther("1000"));
    await corn.connect(liquidator).approve(await lending.getAddress(), ethers.parseEther("1000"));
  });

  it("Should block liquidation during the 24-hour grace period", async function () {
    // 1. User adds collateral
    await lending.connect(user).addCollateral({ value: DEPOSIT_AMOUNT });

    // 2. User borrows maximum amount possible (around 8.33 CORN since collateral ratio is 120%)
    const maxBorrow = await lending.getMaxBorrowAmount(DEPOSIT_AMOUNT);
    await lending.connect(user).borrowCorn(maxBorrow);

    let hf = await lending.getHealthFactor(user.address);
    console.log("Initial Health Factor:", ethers.formatEther(hf));

    // 3. Crash ETH price using MovePrice (selling ETH for CORN)
    // We send some ETH to MovePrice first
    await owner.sendTransaction({ to: await movePrice.getAddress(), value: ethers.parseEther("50") });
    await movePrice.movePrice(ethers.parseEther("40")); // Buy CORN with ETH to crash ETH price relative to CORN

    // Trigger risk timestamp update
    await lending.connect(user).addCollateral({ value: 1n });

    hf = await lending.getHealthFactor(user.address);
    const price = await cornDEX.currentPrice();
    console.log("Crashed Price (ETH in CORN):", ethers.formatEther(price));
    console.log("Crashed Health Factor:", ethers.formatEther(hf));

    expect(hf).to.be.below(ethers.parseEther("1.0"));
    expect(await lending.isLiquidatable(user.address)).to.be.true;

    // 4. Attempt to liquidate immediately - should fail
    await expect(lending.connect(liquidator).liquidate(user.address))
      .to.be.revertedWithCustomError(lending, "Lending__GracePeriodNotOver");

    console.log("Liquidation blocked as expected during grace period.");

    // 5. Fast-forward time by 25 hours
    await network.provider.send("evm_increaseTime", [25 * 3600]);
    await network.provider.send("evm_mine");
    // Also trigger update risk timestamp to be sure
    await lending.connect(user).addCollateral({ value: 1n });

    // 6. Attempt to liquidate after grace period - should succeed
    // liquidator needs to approve Lending to spend their CORN
    await corn.connect(liquidator).approve(await lending.getAddress(), ethers.parseEther("1000"));
    const tx = await lending.connect(liquidator).liquidate(user.address);
    await tx.wait();

    console.log("Liquidation successful after 25 hours.");

    const finalBorrowed = await lending.s_userBorrowed(user.address);
    expect(finalBorrowed).to.equal(0);
  });

  it("Should reset grace period if Health Factor goes back above 1.0", async function () {
    await lending.connect(user).addCollateral({ value: DEPOSIT_AMOUNT });
    const maxBorrow = await lending.getMaxBorrowAmount(DEPOSIT_AMOUNT);
    await lending.connect(user).borrowCorn(maxBorrow);

    // Crash price
    await owner.sendTransaction({ to: await movePrice.getAddress(), value: ethers.parseEther("50") });
    await movePrice.movePrice(ethers.parseEther("40"));

    expect(await lending.getHealthFactor(user.address)).to.be.below(ethers.parseEther("1.0"));
    // Ensure the contract sees the risk
    // Let's call a dummy update or just borrow 1 more wei if possible.
    await lending.connect(user).addCollateral({ value: 1 });

    const riskTime = await lending.s_riskTimestamp(user.address);
    expect(riskTime).to.be.gt(0n);

    // User adds more collateral to recover
    await lending.connect(user).addCollateral({ value: ethers.parseEther("100") });

    expect(await lending.getHealthFactor(user.address)).to.be.above(ethers.parseEther("1.0"));
    expect(await lending.s_riskTimestamp(user.address)).to.equal(0);

    console.log("Risk timestamp reset after adding collateral.");
  });
});
