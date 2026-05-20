// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Orkut20
 * @dev Contrato de Identidade e Reputação para o Projeto Orkut 2.0 (Substrato 335)
 *      Enforces canonical invariants: Ghost (0.5775), Loopseal (0.3490), Gap Soberano (0.9999)
 */
contract Orkut20 {
    // Invariantes escalados (x 10000)
    uint256 public constant GHOST = 5775;       // ~0.577553
    uint256 public constant LOOPSEAL = 3490;    // ~0.349066
    uint256 public constant GAP_MAX = 9999;     // 0.9999

    struct ResearcherProfile {
        string orcid;
        string arkheToken;
        uint256 phiCReputation; // Escala 0-10000
        bool isActive;
    }

    struct Scrap {
        address author;
        string contentCID;      // IPFS/Ceramic CID
        uint256 timestamp;
        uint256 visibilityScore; // Escala 0-10000
    }

    mapping(address => ResearcherProfile) public profiles;
    mapping(address => mapping(address => uint256)) public connections; // address -> friend -> seal

    Scrap[] public scraps;

    event ProfileCreated(address indexed user, string orcid, uint256 phiCReputation);
    event ConnectionAnchored(address indexed user1, address indexed user2, uint256 seal);
    event ScrapPosted(address indexed author, string contentCID, uint256 index);
    event ModerationApplied(uint256 scrapIndex, uint256 newVisibility);

    function createProfile(string memory _orcid, string memory _arkheToken) external {
        require(!profiles[msg.sender].isActive, "Profile already exists");

        profiles[msg.sender] = ResearcherProfile({
            orcid: _orcid,
            arkheToken: _arkheToken,
            phiCReputation: GHOST, // Inicia na base Ghost
            isActive: true
        });

        emit ProfileCreated(msg.sender, _orcid, GHOST);
    }

    function anchorConnection(address _friend) external {
        require(profiles[msg.sender].isActive, "Sender must have a profile");
        require(profiles[_friend].isActive, "Friend must have a profile");

        // Loopseal simulation: uint256 cast of hash
        uint256 seal = uint256(keccak256(abi.encodePacked(msg.sender, _friend, block.timestamp, LOOPSEAL)));

        connections[msg.sender][_friend] = seal;
        connections[_friend][msg.sender] = seal;

        emit ConnectionAnchored(msg.sender, _friend, seal);
    }

    function postScrap(string memory _contentCID) external {
        require(profiles[msg.sender].isActive, "Must have active profile");

        scraps.push(Scrap({
            author: msg.sender,
            contentCID: _contentCID,
            timestamp: block.timestamp,
            visibilityScore: 10000
        }));

        emit ScrapPosted(msg.sender, _contentCID, scraps.length - 1);
    }

    function moderateScrap(uint256 _scrapIndex, bool _isPositive) external {
        require(profiles[msg.sender].isActive, "Must have active profile");
        require(_scrapIndex < scraps.length, "Invalid scrap index");

        uint256 voterWeight = profiles[msg.sender].phiCReputation;
        Scrap storage scrap = scraps[_scrapIndex];

        if (!_isPositive) {
            // Negative moderation impact proportionally
            uint256 impact = voterWeight / 10;
            if (scrap.visibilityScore >= impact) {
                scrap.visibilityScore -= impact;
            } else {
                scrap.visibilityScore = 0;
            }
        }

        emit ModerationApplied(_scrapIndex, scrap.visibilityScore);
    }

    function updateReputation(address _user, uint256 _increase) external {
        require(profiles[_user].isActive, "User not found");

        profiles[_user].phiCReputation += _increase;
        if (profiles[_user].phiCReputation >= GAP_MAX) {
            profiles[_user].phiCReputation = GAP_MAX - 1; // Enforcement of Gap Soberano
        }
    }
}
