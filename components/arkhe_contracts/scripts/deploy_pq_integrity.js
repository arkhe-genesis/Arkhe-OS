const hre = require("hardhat");

async function main() {
  const ArkheChainPQIntegrity = await hre.ethers.getContractFactory("ArkheChainPQIntegrity");
  const contract = await ArkheChainPQIntegrity.deploy();
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  console.log(`ArkheChainPQIntegrity deployed to ${address}`);
  console.log(`Current Block: ${await contract.currentBlock()}`);
}

main().catch(console.error);
