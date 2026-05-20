// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/TemporalMerkleCondition.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envOr("PRIVATE_KEY", uint256(0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80));

        vm.startBroadcast(deployerPrivateKey);

        TemporalMerkleCondition condition = new TemporalMerkleCondition();

        // Register humility score for test address 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (Anvil account 0)
        address testUser = vm.addr(deployerPrivateKey);
        condition.setUserHumility(testUser, 9000); // 0.9000 > Ghost threshold

        vm.stopBroadcast();

        console.log("TemporalMerkleCondition deployed at:", address(condition));
    }
}
