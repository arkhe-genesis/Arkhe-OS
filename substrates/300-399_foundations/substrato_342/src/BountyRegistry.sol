// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";

contract BountyRegistry is Ownable {
    struct Bounty {
        uint256 bountyId;
        address sponsor;
        string title;
        string descriptionCid;
        uint256 rewardUsdc;
        uint256 deadline;
        address assignee;
        string solutionCid;
        string status;
    }

    mapping(uint256 => Bounty) public bounties;
    uint256 public bountyCount;

    address public paymentFacilitator;

    event BountyCreated(uint256 indexed bountyId, address indexed sponsor, string title, uint256 reward);
    event BountyAssigned(uint256 indexed bountyId, address indexed assignee);
    event SolutionSubmitted(uint256 indexed bountyId, string solutionCid);
    event BountyApproved(uint256 indexed bountyId, uint256 paidAmount, string txHash);

    function setPaymentFacilitator(address _facilitator) external onlyOwner {
        paymentFacilitator = _facilitator;
    }

    function createBounty(string calldata title, string calldata descriptionCid, uint256 rewardUsdc, uint256 deadlineDays) external returns (uint256) {
        bountyCount++;
        bounties[bountyCount] = Bounty({
            bountyId: bountyCount,
            sponsor: msg.sender,
            title: title,
            descriptionCid: descriptionCid,
            rewardUsdc: rewardUsdc,
            deadline: block.timestamp + (deadlineDays * 1 days),
            assignee: address(0),
            solutionCid: "",
            status: "OPEN"
        });

        emit BountyCreated(bountyCount, msg.sender, title, rewardUsdc);
        return bountyCount;
    }
}
