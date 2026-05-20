// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/TemporalMerkleCondition.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerPrivateKey);

        TemporalMerkleCondition condition = new TemporalMerkleCondition();

        // Register humility score for test address (derived from deployer)
        address testUser = vm.addr(deployerPrivateKey);
        condition.setUserHumility(testUser, 9000); // 0.9000 > Ghost threshold

        vm.stopBroadcast();

        console.log("TemporalMerkleCondition deployed at:", address(condition));
    }
}
