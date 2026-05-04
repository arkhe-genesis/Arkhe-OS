// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract DynamicOracleGovernance is Ownable {
    struct OracleSource {
        string name;           // ex: "chainlink", "api3", "pyth"
        string endpoint;       // URL ou identificador
        uint256 weight;        // peso na agregação (x1000 para precisão)
        bool active;
    }

    mapping(string => OracleSource) public sources;
    string[] public sourceList;
    IERC20 public governanceToken;

    event SourceAdded(string name, string endpoint, uint256 weight);
    event SourceRemoved(string name);
    event WeightUpdated(string name, uint256 newWeight);

    constructor(address _token) {
        governanceToken = IERC20(_token);
    }

    modifier onlyGovernance() {
        require(governanceToken.balanceOf(msg.sender) >= 1000 ether, "Not enough governance tokens");
        _;
    }

    function addSource(string memory name, string memory endpoint, uint256 weight) external onlyGovernance {
        require(!sources[name].active, "Source already exists");
        sources[name] = OracleSource(name, endpoint, weight, true);
        sourceList.push(name);
        emit SourceAdded(name, endpoint, weight);
    }

    function removeSource(string memory name) external onlyGovernance {
        require(sources[name].active, "Source not active");
        sources[name].active = false;
        emit SourceRemoved(name);
    }

    function updateWeight(string memory name, uint256 newWeight) external onlyGovernance {
        require(sources[name].active, "Source not active");
        sources[name].weight = newWeight;
        emit WeightUpdated(name, newWeight);
    }

    function getActiveSources() external view returns (string[] memory names, string[] memory endpoints, uint256[] memory weights) {
        uint activeCount = 0;
        for (uint i=0; i<sourceList.length; i++) {
            if (sources[sourceList[i]].active) activeCount++;
        }
        names = new string[](activeCount);
        endpoints = new string[](activeCount);
        weights = new uint256[](activeCount);
        uint idx = 0;
        for (uint i=0; i<sourceList.length; i++) {
            if (sources[sourceList[i]].active) {
                names[idx] = sourceList[i];
                endpoints[idx] = sources[sourceList[i]].endpoint;
                weights[idx] = sources[sourceList[i]].weight;
                idx++;
            }
        }
    }
}
