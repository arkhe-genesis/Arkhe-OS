// contracts/ResourceOracle.sol — Chainlink Functions
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@chainlink/contracts/src/v0.8/functions/dev/v1_0_0/FunctionsClient.sol";
import "@chainlink/contracts/src/v0.8/shared/access/ConfirmedOwner.sol";

contract ResourceOracle is FunctionsClient, ConfirmedOwner {
    // Mapeamento de recurso → preço em ARK (token nativo)
    mapping(string => uint256) public resourcePrices;

    // Eventos para atualização de preços
    event PriceUpdated(string indexed resource, uint256 price, uint256 timestamp);

    constructor(address router) FunctionsClient(router) ConfirmedOwner(msg.sender) {}

    /**
     * @dev Solicita preço de recurso via Chainlink Functions
     * @param resource Nome do recurso (ex: "energy_gj", "compute_tflops")
     * @param source Código JavaScript para buscar preço de API externa
     */
    function requestResourcePrice(
        string calldata resource,
        string calldata source
    ) external returns (bytes32 requestId) {
        // Preparar request para Chainlink Functions
        requestId = _sendRequest(
            source,
            "",  // secrets (opcional)
            new string[](0),  // args (empty array since we pass resource as argument in js)
            new bytes[](0),
            300000,  // gas limit
            0  // subscription ID (pay-per-request)
        );

        // Armazenar mapeamento requestId → resource
        // (implementação simplificada)
        return requestId;
    }

    /**
     * @dev Callback do Chainlink Functions com preço obtido
     */
    function fulfillRequest(
        bytes32 requestId,
        bytes calldata response,
        bytes calldata err
    ) internal override {
        require(err.length == 0, "Chainlink Functions error");

        // Decodificar resposta JSON: {"resource": "energy_gj", "price": 12345}
        // (usar Chainlink Functions decoder ou biblioteca externa)

        // Atualizar preço no mapping
        // emit PriceUpdated(resource, price, block.timestamp);
    }

    /**
     * @dev Consulta preço atual de recurso
     */
    function getPrice(string calldata resource) external view returns (uint256) {
        return resourcePrices[resource];
    }
}
