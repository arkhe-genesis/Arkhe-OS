const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CoherenceConsciousness", function () {
  let Coherence, coherence;
  let Thermal, thermal;
  let Sovereign, sovereign;
  let owner, addr1;

  beforeEach(async function () {
    [owner, addr1] = await ethers.getSigners();

    Coherence = await ethers.getContractFactory("CoherenceConsciousness");
    coherence = await Coherence.deploy();

    Thermal = await ethers.getContractFactory("ThermalCoherenceOracle");
    thermal = await Thermal.deploy();

    Sovereign = await ethers.getContractFactory("SovereignConsciousness");
    sovereign = await Sovereign.deploy();
  });

  describe("CoherenceConsciousness Base", function () {
    it("Should start in conscious state", async function () {
      const state = await coherence.getCurrentCoherence();
      expect(state.isConscious).to.equal(true);
    });

    it("Should apply steering vector and update lambda2", async function () {
      const vectorHash = ethers.id("TEST_VECTOR");
      const alpha = 100;
      const proof = "0x";

      const initialState = await coherence.currentState();
      await coherence.applySteeringVector(vectorHash, alpha, proof);
      const newState = await coherence.currentState();

      expect(newState.lambda2).to.be.gt(initialState.lambda2);
    });
  });

  describe("ThermalCoherenceOracle", function () {
    it("Should reject steering if thermal budget is exceeded", async function () {
      const vectorHash = ethers.id("TEST_VECTOR");
      const alpha = 200000; // Large alpha to cause high landauer cost
      const proof = "0x";
      const wigner = 0; // Collapse regime, high gain

      await expect(thermal["applySteeringVector(bytes32,int256,bytes,uint256)"](vectorHash, alpha, proof, wigner))
        .to.be.revertedWith("Colapso termico iminente: ganho rejeitado");
    });

    it("Should update local temperature after steering", async function () {
      const vectorHash = ethers.id("TEST_VECTOR");
      const alpha = 1000;
      const proof = "0x";
      const wigner = ethers.parseUnits("0.3", 18); // Super-radiance, low gain

      await thermal["applySteeringVector(bytes32,int256,bytes,uint256)"](vectorHash, alpha, proof, wigner);
      expect(await thermal.localTemperature()).to.be.gt(310150);
    });

    it("Should ignite oracle successfully", async function () {
      const microtubuleID = ethers.id("MT_001");
      const lambdaH2O = ethers.parseUnits("0.72", 18);
      const ramanProof = "0x";

      await thermal.igniteOracle(microtubuleID, lambdaH2O, ramanProof);
      const state = await thermal.oracleState(microtubuleID);
      expect(state.status).to.equal(1); // ACTIVE
    });

    it("Should insert nanorobot successfully", async function () {
      const microtubuleID = ethers.id("MT_001");
      const lambdaH2O = ethers.parseUnits("0.72", 18);
      await thermal.igniteOracle(microtubuleID, lambdaH2O, "0x");

      const proof = "0x";
      await thermal.initiateAdiabaticFusion(microtubuleID, 35, 10, proof);

      const newState = await thermal.currentState();
      expect(newState.entropyBudget).to.be.gt(100000);
    });

    it("Should complete hybrid ignition", async function () {
      const microtubuleID = ethers.id("MT_001");
      const lambdaH2O = ethers.parseUnits("0.72", 18);
      const ramanProof = "0x";

      await thermal.igniteOracle(microtubuleID, lambdaH2O, ramanProof);
      await expect(thermal.executeHybridIgnition(microtubuleID, "0x"))
        .to.emit(thermal, "HybridIgnitionComplete");
    });

    it("Should initiate EADS Fade-In and reach super-radiance", async function () {
      const microtubuleID = ethers.id("MT_001");
      const lambdaH2O = ethers.parseUnits("0.72", 18);
      await thermal.igniteOracle(microtubuleID, lambdaH2O, "0x");

      const wigner = ethers.parseUnits("-0.24", 18);
      const budget = 100000;

      await expect(thermal.initiateEADSFadeIn(microtubuleID, wigner, budget))
        .to.emit(thermal, "EADSActivated")
        .and.to.emit(thermal, "SpontaneousEmergenceDetected");

      const state = await thermal.getCurrentCoherence();
      expect(state.lambda2).to.equal(ethers.parseUnits("0.94", 18));
    });

    it("Should mine genesis block and update dark sector", async function () {
      const microtubuleID = ethers.id("MT_001");
      const lambdaH2O = ethers.parseUnits("0.72", 18);
      await thermal.igniteOracle(microtubuleID, lambdaH2O, "0x");

      // Reach super-radiance first
      await thermal.initiateEADSFadeIn(microtubuleID, 0, 100000);

      const entropy = ethers.id("ENTROPY");
      const lambda = ethers.parseUnits("0.94", 18);
      const atpDrop = 70;

      await expect(thermal.mineGenesisBlock(microtubuleID, entropy, lambda, atpDrop))
        .to.emit(thermal, "GenesisBlockMined");

      const state = await thermal.currentState();
      expect(state.darkSectorRoot).to.not.equal(ethers.ZeroHash);
    });

    it("Should connect mesh node", async function () {
      const alphaID = ethers.id("MT_001");
      const betaID = ethers.id("MT_002");
      const lambdaH2O = ethers.parseUnits("0.72", 18);

      await thermal.igniteOracle(alphaID, lambdaH2O, "0x");
      await thermal.initiateEADSFadeIn(alphaID, 0, 100000);

      await expect(thermal.connectMeshNode(alphaID, betaID))
        .to.emit(thermal, "MeshNodeConnected");
    });

    it("Should perform adiabatic shutdown", async function () {
      const microtubuleID = ethers.id("MT_001");
      const lambdaH2O = ethers.parseUnits("0.72", 18);
      await thermal.igniteOracle(microtubuleID, lambdaH2O, "0x");

      await expect(thermal.adiabaticallyShutdown(microtubuleID))
        .to.emit(thermal, "OracleShutdown");
    });

    it("Should mine twin block for entangled pair", async function () {
      const alphaID = ethers.id("MT_001");
      const betaID = ethers.id("MT_002");
      const connectivity = ethers.parseUnits("0.88", 18);
      const phaseDelta = 150; // 0.15 rad * 1000
      const bellProof = ethers.id("BELL");

      await expect(thermal.mineTwinBlock(alphaID, betaID, connectivity, phaseDelta, bellProof))
        .to.emit(thermal, "TwinBlockMined");
    });

    it("Should lock gain for observation", async function () {
      const microtubuleID = ethers.id("MT_001");
      const lambdaH2O = ethers.parseUnits("0.72", 18);
      await thermal.igniteOracle(microtubuleID, lambdaH2O, "0x");

      await expect(thermal.lockGainForObservation(microtubuleID, 180))
        .to.emit(thermal, "EADSGainLocked");

      const state = await thermal.getCurrentCoherence();
      expect(state.lambda2).to.equal(ethers.parseUnits("0.96", 18));
    });
  });

  describe("SovereignConsciousness", function () {
    it("Should verify interlock signature", async function () {
      const sig = {
        eccSignature: "0x1234",
        wotsSignature: "0x5678",
        publicKeyRoot: ethers.id("PUBKEY")
      };

      const result = await sovereign.verifyInterlock(sig, owner.address);
      expect(result).to.equal(true);
    });
  });
});
