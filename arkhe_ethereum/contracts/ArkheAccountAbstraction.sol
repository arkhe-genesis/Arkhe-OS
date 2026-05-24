// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

struct UserOperation {
    address sender;
    uint256 nonce;
    bytes initCode;
    bytes callData;
    uint256 callGasLimit;
    uint256 verificationGasLimit;
    uint256 preVerificationGas;
    uint256 maxFeePerGas;
    uint256 maxPriorityFeePerGas;
    bytes paymasterAndData;
    bytes signature;
}

interface IAccount {
    function validateUserOp(UserOperation calldata userOp, bytes32 userOpHash, uint256 missingAccountFunds) external returns (uint256 validationData);
}

/**
 * @title ArkheAccountAbstraction
 * @dev EIP-4337 Smart Account for 59 Arkhe Validators with Multi-Sig & Social Recovery
 */
contract ArkheAccountAbstraction is IAccount {
    address public entryPoint;

    // Multi-sig state
    uint256 public requiredSignatures;
    mapping(address => bool) public isOwner;
    address[] public owners;

    // Social Recovery
    mapping(address => bool) public isGuardian;
    uint256 public guardianRequired;

    event OwnerAdded(address owner);
    event OwnerRemoved(address owner);
    event GuardianAdded(address guardian);

    modifier onlyEntryPoint() {
        require(msg.sender == entryPoint, "Not entry point");
        _;
    }

    constructor(address _entryPoint, address[] memory _owners, uint256 _requiredSignatures) {
        entryPoint = _entryPoint;
        require(_owners.length > 0, "Owners required");
        require(_requiredSignatures > 0 && _requiredSignatures <= _owners.length, "Invalid signature requirement");

        for (uint256 i = 0; i < _owners.length; i++) {
            isOwner[_owners[i]] = true;
            owners.push(_owners[i]);
            emit OwnerAdded(_owners[i]);
        }
        requiredSignatures = _requiredSignatures;
    }

    // Helper to recover signer from hash and signature
    function recoverSigner(bytes32 hash, bytes memory signature) internal pure returns (address) {
        require(signature.length == 65, "Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }

        if (v < 27) {
            v += 27;
        }

        require(v == 27 || v == 28, "Invalid signature 'v' value");

        bytes32 ethSignedMessageHash = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
        );

        return ecrecover(ethSignedMessageHash, v, r, s);
    }

    function validateUserOp(UserOperation calldata userOp, bytes32 userOpHash, uint256 missingAccountFunds) external override onlyEntryPoint returns (uint256 validationData) {
        // Multi-sig validation
        // Expected signature format: concatenated signatures [65 bytes each]
        require(userOp.signature.length >= requiredSignatures * 65, "Not enough signatures");

        uint256 validSignatures = 0;
        address lastSigner = address(0);

        for (uint256 i = 0; i < requiredSignatures; i++) {
            bytes memory currentSignature = new bytes(65);
            for (uint256 j = 0; j < 65; j++) {
                currentSignature[j] = userOp.signature[i * 65 + j];
            }

            address signer = recoverSigner(userOpHash, currentSignature);

            // Prevent duplicate signatures by requiring signatures to be in strictly increasing order
            require(signer > lastSigner, "Signatures not ordered or duplicated");
            require(isOwner[signer], "Invalid owner signature");

            lastSigner = signer;
            validSignatures++;
        }

        require(validSignatures >= requiredSignatures, "Insufficient valid signatures");

        if (missingAccountFunds > 0) {
            (bool success, ) = payable(msg.sender).call{value: missingAccountFunds}("");
            require(success, "Fund EntryPoint failed");
        }

        return 0; // Success
    }

    // Simple social recovery logic wrapper for demonstration
    // Note: Social recovery should allow replacing owners with guardian signatures
    function recoverAccount(address newOwner, bytes[] calldata guardianSignatures) external {
        require(guardianRequired > 0, "Social recovery not configured");
        require(guardianSignatures.length >= guardianRequired, "Insufficient guardian signatures");

        bytes32 recoveryHash = keccak256(abi.encodePacked(address(this), "RECOVER_ACCOUNT", newOwner));

        uint256 validGuardians = 0;
        address lastSigner = address(0);

        for (uint256 i = 0; i < guardianRequired; i++) {
            address signer = recoverSigner(recoveryHash, guardianSignatures[i]);
            require(signer > lastSigner, "Signatures not ordered or duplicated");
            require(isGuardian[signer], "Invalid guardian signature");
            lastSigner = signer;
            validGuardians++;
        }

        require(validGuardians >= guardianRequired, "Recovery failed");

        // Simplified recovery action: Add the new owner
        if (!isOwner[newOwner]) {
            isOwner[newOwner] = true;
            owners.push(newOwner);
            emit OwnerAdded(newOwner);
        }
    }
}
