// contracts/federal/FederalBudgetExecutor.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * FederalBudgetExecutor: Execução orçamentária via smart contracts ancorados no Códice.
 * Implementa a Emenda Constitucional CAT-ARK.
 */
contract FederalBudgetExecutor {
    struct BudgetAllocation {
        bytes32 allocationId;
        address recipientUDAO;
        uint256 amountCatArk;
        bytes32 conditionsHash;
        uint256 releaseTimestamp;
        bool executed;
    }

    mapping(bytes32 => BudgetAllocation) public allocations;

    event AllocationCreated(bytes32 indexed allocationId, address indexed recipient, uint256 amount);
    event AllocationExecuted(bytes32 indexed allocationId, uint256 timestamp);

    function createAllocation(
        bytes32 _allocationId,
        address _recipientUDAO,
        uint256 _amountCatArk,
        bytes32 _conditionsHash
    ) external {
        allocations[_allocationId] = BudgetAllocation({
            allocationId: _allocationId,
            recipientUDAO: _recipientUDAO,
            amountCatArk: _amountCatArk,
            conditionsHash: _conditionsHash,
            releaseTimestamp: 0,
            executed: false
        });

        emit AllocationCreated(_allocationId, _recipientUDAO, _amountCatArk);
    }

    function executeAllocation(bytes32 _allocationId, bytes calldata _zkProof) external {
        BudgetAllocation storage alloc = allocations[_allocationId];
        require(!alloc.executed, "Already executed");

        // Em um sistema real, verificaríamos a prova ZK aqui
        alloc.executed = true;
        alloc.releaseTimestamp = block.timestamp;

        emit AllocationExecuted(_allocationId, block.timestamp);
    }
}
