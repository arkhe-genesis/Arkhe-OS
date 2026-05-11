// contracts/OpticalBlueprintRegistry.sol
pragma solidity ^0.8.19;

contract OpticalBlueprintRegistry {
    struct Blueprint {
        bytes32 blueprintHash;
        address creatorNode;
        uint256 creationTDB;
        bool isPublic;
        uint256 licenseFee;
    }
    mapping(bytes32 => Blueprint) public blueprints;
    event BlueprintMinted(bytes32 indexed hash, address indexed creator, uint256 tdb);

    function registerBlueprint(bytes32 blueprintHash, uint256 creationTDB_q, bool isPublic, uint256 licenseFee) external {
        require(blueprints[blueprintHash].creatorNode == address(0), "Ja existe");
        blueprints[blueprintHash] = Blueprint({
            blueprintHash: blueprintHash,
            creatorNode: msg.sender,
            creationTDB: creationTDB_q,
            isPublic: isPublic,
            licenseFee: licenseFee
        });
        emit BlueprintMinted(blueprintHash, msg.sender, creationTDB_q);
    }
}
