const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("Arkhe Security and OTOF Subsidy", function () {
  let subsidy;
  let integration;
  let rio;
  let mockVerifier;
  let admin, clinic, patient, attacker;
  let sensors = [];
  const GENETIC_HASH = ethers.keccak256(ethers.toUtf8Bytes("ATGC...salt123"));
  const NULLIFIER_HASH = ethers.keccak256(ethers.toUtf8Bytes("nullifier123"));
  const MAXTOKI_PROOF = ethers.keccak256(ethers.toUtf8Bytes("maxtoki_prediction"));
  const ZK_PROOF_A = [0, 0];
  const ZK_PROOF_B = [[0, 0], [0, 0]];
  const ZK_PROOF_C = [0, 0];
  const PUBLIC_INPUTS = [0, NULLIFIER_HASH, GENETIC_HASH];

  beforeEach(async function () {
    [admin, clinic, patient, attacker] = await ethers.getSigners();
    sensors = [];

    const MockRIO = await ethers.getContractFactory("MockRIOToken");
    rio = await MockRIO.deploy();

    const Subsidy = await ethers.getContractFactory("ArkheOTOFSubsidyManager");
    subsidy = await Subsidy.deploy(await rio.getAddress());

    const MockVerifier = await ethers.getContractFactory("MockVerifier");
    mockVerifier = await MockVerifier.deploy();

    const Integration = await ethers.getContractFactory("ArkheOTOFIntegration");
    integration = await Integration.deploy(await mockVerifier.getAddress(), await subsidy.getAddress());

    // Register sensors
    for (let i = 0; i < 168; i++) {
      const wallet = ethers.Wallet.createRandom().connect(ethers.provider);
      sensors.push(wallet);
      await subsidy.registerSensor(i, wallet.address);
    }

    const DAO_GOVERNANCE = await subsidy.DAO_GOVERNANCE();
    const NV_SENSOR_NODE = await subsidy.NV_SENSOR_NODE();
    const CLINIC_ORACLE = await subsidy.CLINIC_ORACLE();
    await subsidy.grantRole(DAO_GOVERNANCE, admin.address);
    await subsidy.grantRole(NV_SENSOR_NODE, admin.address);
    await subsidy.grantRole(CLINIC_ORACLE, clinic.address);
    await subsidy.authorizeClinic(clinic.address, true);
  });

  async function performGeneticVerification() {
    await integration.connect(patient).verifyEligibility(
        ZK_PROOF_A, ZK_PROOF_B, ZK_PROOF_C, PUBLIC_INPUTS,
        85, 90, 10
    );
  }

  it("Test 1: Byzantine Sensor Attack (Insufficient consensus)", async function () {
    const fakeLambda = 5000;
    const sigs = [];
    const ids = [];
    const timestamp = await time.latest();

    // Only 56 sensors sign (1/3)
    for (let i = 0; i < 56; i++) {
      ids.push(i);
      const message = ethers.solidityPackedKeccak256(
        ["bytes32", "uint256", "uint256"],
        [GENETIC_HASH, fakeLambda, timestamp]
      );
      const sig = await sensors[i].signMessage(ethers.getBytes(message));
      sigs.push(sig);
    }

    await expect(
      subsidy.connect(admin).validateCoherenceConsensus(GENETIC_HASH, fakeLambda, timestamp, sigs, ids)
    ).to.be.revertedWith("INSUFFICIENT_SENSOR_CONSENSUS");
  });

  it("Test 4: Temporal Gravity Calculation", async function () {
    await performGeneticVerification();
    await subsidy.connect(clinic).enrollPatientTemporal(
      GENETIC_HASH,
      NULLIFIER_HASH,
      patient.address,
      ethers.parseEther("1000"),
      8500,
      30,
      MAXTOKI_PROOF
    );

    const p = await subsidy.patients(GENETIC_HASH);
    expect(p.wallet).to.equal(patient.address);
  });

  it("Test 5: Emergency Circuit Breaker", async function () {
    await performGeneticVerification();
    // Enroll patient first
    await subsidy.connect(clinic).enrollPatientTemporal(
      GENETIC_HASH,
      NULLIFIER_HASH,
      patient.address,
      ethers.parseEther("1000"),
      8500,
      30,
      MAXTOKI_PROOF
    );

    const criticalLambda = 4500;
    const sigs = [];
    const ids = [];
    const timestamp = await time.latest() + 10;
    await time.increaseTo(timestamp);

    for (let i = 0; i < 112; i++) {
      ids.push(i);
      const message = ethers.solidityPackedKeccak256(
        ["bytes32", "uint256", "uint256"],
        [GENETIC_HASH, criticalLambda, timestamp]
      );
      const sig = await sensors[i].signMessage(ethers.getBytes(message));
      sigs.push(sig);
    }

    await subsidy.connect(admin).validateCoherenceConsensus(GENETIC_HASH, criticalLambda, timestamp, sigs, ids);

    const p = await subsidy.patients(GENETIC_HASH);
    expect(p.status).to.equal(6); // TreatmentStatus.EmergencyStop
  });

  it("Test 6: Privacy - Nullifier Prevention", async function () {
    await performGeneticVerification();
    await subsidy.connect(clinic).enrollPatientTemporal(
      GENETIC_HASH,
      NULLIFIER_HASH,
      patient.address,
      ethers.parseEther("1000"),
      8500,
      30,
      MAXTOKI_PROOF
    );

    await expect(
      subsidy.connect(clinic).enrollPatientTemporal(
        ethers.keccak256(ethers.toUtf8Bytes("other_hash")),
        NULLIFIER_HASH,
        patient.address,
        ethers.parseEther("1000"),
        8500,
        30,
        MAXTOKI_PROOF
      )
    ).to.be.revertedWith("NULLIFIER_SPENT");
  });

  it("Test 7: Full Milestone Execution Flow", async function () {
    const totalCost = ethers.parseEther("1000");
    await performGeneticVerification();
    await subsidy.connect(clinic).enrollPatientTemporal(
      GENETIC_HASH,
      NULLIFIER_HASH,
      patient.address,
      totalCost,
      8500,
      30,
      MAXTOKI_PROOF
    );

    // Mint RIO to the contract for subsidy
    await rio.mint(await subsidy.getAddress(), totalCost);

    // Milestone 1 (Injection)
    const timestamp0 = await time.latest() + 100;
    await time.increaseTo(timestamp0);
    const sigs0 = [];
    const ids0 = [];
    for (let i = 0; i < 112; i++) {
        ids0.push(i);
        const message = ethers.solidityPackedKeccak256(
            ["bytes32", "uint256", "uint256"],
            [GENETIC_HASH, 8500, timestamp0]
        );
        const sig = await sensors[i].signMessage(ethers.getBytes(message));
        sigs0.push(sig);
    }
    await subsidy.connect(admin).validateCoherenceConsensus(GENETIC_HASH, 8500, timestamp0, sigs0, ids0);
    await subsidy.connect(clinic).executeTemporalMilestone(GENETIC_HASH, 0, MAXTOKI_PROOF);

    // Milestone 2 (Recovery) - Day 30
    await time.increase(30 * 24 * 60 * 60);
    const lambdaReading = 8500;
    const timestamp2 = await time.latest();
    const sigs2 = [];
    const ids2 = [];

    for (let i = 0; i < 112; i++) {
      ids2.push(i);
      const message = ethers.solidityPackedKeccak256(
        ["bytes32", "uint256", "uint256"],
        [GENETIC_HASH, lambdaReading, timestamp2]
      );
      const sig = await sensors[i].signMessage(ethers.getBytes(message));
      sigs2.push(sig);
    }

    await subsidy.connect(admin).validateCoherenceConsensus(GENETIC_HASH, lambdaReading, timestamp2, sigs2, ids2);

    await subsidy.connect(clinic).executeTemporalMilestone(GENETIC_HASH, 1, MAXTOKI_PROOF);

    const p = await subsidy.patients(GENETIC_HASH);
    expect(p.paidAmount).to.be.gt(0);
    expect(p.status).to.equal(3); // Recovery
  });

  describe("RioOTOFGovernor", function () {
    let governor;
    let timelock;

    beforeEach(async function () {
        const Timelock = await ethers.getContractFactory("TimelockController");
        // Simple timelock setup
        timelock = await Timelock.deploy(0, [], [], admin.address);

        const Governor = await ethers.getContractFactory("RioOTOFGovernor");
        governor = await Governor.deploy(await rio.getAddress(), await timelock.getAddress());

        // Grant roles
        const PROPOSER_ROLE = await timelock.PROPOSER_ROLE();
        const EXECUTOR_ROLE = await timelock.EXECUTOR_ROLE();
        await timelock.grantRole(PROPOSER_ROLE, await governor.getAddress());
        await timelock.grantRole(EXECUTOR_ROLE, ethers.ZeroAddress); // Anyone can execute

        const BURNER_ROLE = await rio.BURNER_ROLE();
        await rio.grantRole(BURNER_ROLE, await governor.getAddress());

        // Mint and delegate for voting power
        await rio.mint(admin.address, ethers.parseEther("10000"));
        await rio.delegate(admin.address);
        await time.advanceBlock();
    });

    it("Test 8: Quadratic Voting Logic", async function () {
        const amount = ethers.parseEther("100");
        const justification = "ipfs://Qm...";
        const lambdaMin = 8500;

        // Create proposal
        const tx = await governor.proposeMedicalSubsidy(GENETIC_HASH, amount, justification, lambdaMin);
        const receipt = await tx.wait();

        // Find ProposalCreated event log
        const proposalCreatedEvent = receipt.logs.find(log => {
            try {
                return governor.interface.parseLog(log).name === "ProposalCreated";
            } catch (e) {
                return false;
            }
        });
        const proposalId = governor.interface.parseLog(proposalCreatedEvent).args[0];

        await time.advanceBlock(); // Wait for voting delay

        // Vote quadratic: 10 voice credits = 100 RIO cost
        const voiceCredits = 10;
        const expectedCost = BigInt(voiceCredits * voiceCredits);

        const balanceBefore = await rio.balanceOf(admin.address);
        await governor.castVoteQuadratic(proposalId, 1, voiceCredits);
        const balanceAfter = await rio.balanceOf(admin.address);

        expect(balanceBefore - balanceAfter).to.equal(expectedCost);

        const proposal = await governor.medicalProposals(0);
        expect(proposal.forVotes).to.equal(voiceCredits);

        // Check Governor state
        const proposalState = await governor.state(proposalId);
        expect(proposalState).to.equal(1); // Active
    });
  });
});
