// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

import "forge-std/Script.sol";
import "../src/CodeCommitRegistryHashtree.sol";
import "../src/BountyRegistry.sol";
import "../src/x402/BountyPaymentFacilitator.sol";

contract DeployOrkutLabs is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address oracle = vm.envAddress("ORACLE_ADDRESS");
        address usdc = vm.envAddress("USDC_ADDRESS");
        address x402Facilitator = vm.envAddress("X402_FACILITATOR");
        address hashtreeVerifier = vm.envAddress("HASHTREE_VERIFIER");

        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy CodeCommitRegistry com Hashtree
        CodeCommitRegistryHashtree commitRegistry = new CodeCommitRegistryHashtree();
        console.log("CodeCommitRegistry deployed at:", address(commitRegistry));

        // 2. Deploy BountyRegistry
        BountyRegistry bountyRegistry = new BountyRegistry();
        console.log("BountyRegistry deployed at:", address(bountyRegistry));

        // 3. Deploy BountyPaymentFacilitator
        BountyPaymentFacilitator paymentFacilitator = new BountyPaymentFacilitator(
            usdc,
            x402Facilitator,
            address(bountyRegistry)
        );
        console.log("BountyPaymentFacilitator deployed at:", address(paymentFacilitator));

        // 4. Configurar permissões cruzadas
        bountyRegistry.setPaymentFacilitator(address(paymentFacilitator));

        vm.stopBroadcast();

        // 5. Gerar arquivo de configuração para frontend
        string memory config = string.concat(
            '{"commitRegistry":"', vm.toString(address(commitRegistry)), '"',
            ',"bountyRegistry":"', vm.toString(address(bountyRegistry)), '"',
            ',"paymentFacilitator":"', vm.toString(address(paymentFacilitator)), '"',
            ',"network":"sepolia"}'
        );
        vm.writeFile(".deploy-config.json", config);

        console.log(unicode"✅ Deploy completo! Config em .deploy-config.json");
    }
}
