// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MetaReportAggregator {
    struct IndividualReport {
        bytes32 reportHash;
        uint256 timestamp;
        address orchestrator;
    }

    mapping(bytes32 => IndividualReport) public reports; // reportId => report
    bytes32[] public reportIds;

    event ReportSubmitted(bytes32 indexed reportId, address orchestrator);
    event MetaReportGenerated(bytes32 indexed metaHash, uint256 startTs, uint256 endTs, uint256 count);

    function submitReport(bytes32 reportId, bytes32 reportHash) external {
        require(reports[reportId].timestamp == 0, "Report already submitted");
        reports[reportId] = IndividualReport(reportHash, block.timestamp, msg.sender);
        reportIds.push(reportId);
        emit ReportSubmitted(reportId, msg.sender);
    }

    function generateMetaReport(uint256 startTs, uint256 endTs) external view returns (bytes32 metaHash, uint256 count) {
        bytes32[] memory hashes = new bytes32[](reportIds.length);
        count = 0;
        for (uint i=0; i<reportIds.length; i++) {
            IndividualReport storage r = reports[reportIds[i]];
            if (r.timestamp >= startTs && r.timestamp <= endTs) {
                hashes[count] = r.reportHash;
                count++;
            }
        }
        // hash = keccak256(abi.encodePacked(sorted hashes + count))
        assembly {
            // simplificado: concatenar hashes[0..count-1] e count
            let ptr := mload(0x40)
            for { let j := 0 } lt(j, count) { j := add(j,1) } {
                mstore(ptr, mload(add(hashes, mul(j,0x20))))
                ptr := add(ptr, 0x20)
            }
            mstore(ptr, count)
            metaHash := keccak256(ptr, sub(ptr, 0x20))
        }
    }
}
