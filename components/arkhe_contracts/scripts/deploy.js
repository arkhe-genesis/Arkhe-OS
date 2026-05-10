const hre = require("hardhat");

async function main() {
  const { logger } = await import('../../server/logger.ts');
  const [deployer] = await hre.ethers.getSigners();
  logger.info("Deploying contracts with the account: " + deployer.address);

  const TimechainPhase = await hre.ethers.getContractFactory("TimechainPhase");
  const timechainPhase = await TimechainPhase.deploy();

  await timechainPhase.waitForDeployment();

  logger.info("TimechainPhase deployed to: " + await timechainPhase.getAddress());
}

main().catch(async (error) => {
  const { logger } = await import('../../server/logger.ts');
  logger.error(error);
  process.exitCode = 1;
});
