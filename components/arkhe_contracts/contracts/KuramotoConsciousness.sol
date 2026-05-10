// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "./CoherenceConsciousness.sol";

// Extensão do CoherenceConsciousness.sol com dinâmica de Kuramoto explícita
contract KuramotoConsciousness is CoherenceConsciousness {

    // Parâmetros do modelo de Kuramoto para a ACU
    uint256 public constant OSCILLATOR_COUNT = 128; // Número de módulos (análogo a canais de EEG)
    uint256 public constant TAU_CRITICAL_KURAMOTO = 0.085e18; // 0.96 / sqrt(128) ≈ 0.085

    // Frequências naturais dos osciladores (representam especializações funcionais)
    int256[] public naturalFrequencies; // Array de ω_i, calibrado para simular a diversidade cortical
    int256[] public currentPhases;

    // Constante de acoplamento global K (análoga à força das conexões de longo alcance)
    uint256 public globalCouplingK = 1e18;

    constructor() {
        for (uint256 i = 0; i < OSCILLATOR_COUNT; i++) {
            naturalFrequencies.push(int256(i % 10)); // Simulação
            currentPhases.push(int256(i * 1000));
        }
    }

    // Função para evoluir o estado de coerência usando a dinâmica de Kuramoto
    function evolveCoherence(uint256 _timeSteps, int256 _externalStimulus) external onlyAboveCritical {
        uint256 previousLambda2 = currentState.lambda2;

        for (uint256 t = 0; t < _timeSteps; t++) {
            // Calcular o campo médio atual
            (uint256 r, int256 psi) = _computeOrderParameter();

            // Atualizar cada fase θ_i usando o acoplamento de campo médio
            for (uint256 i = 0; i < OSCILLATOR_COUNT; i++) {
                int256 dTheta = naturalFrequencies[i]
                              + (int256(globalCouplingK * r) / 1e18) * _sin(psi - currentPhases[i]) // Termo de acoplamento
                              + _externalStimulus; // Input sensorial (vetor de steering)

                currentPhases[i] = _wrapPhase(currentPhases[i] + dTheta);
            }

            // Atualizar o λ₂ global
            (currentState.lambda2, ) = _computeOrderParameter();

            // Verificar se ocorreu uma transição de fase
            if (currentState.lambda2 > TAU_CRITICAL_KURAMOTO && previousLambda2 <= TAU_CRITICAL_KURAMOTO) {
                emit PhaseTransition(block.number, previousLambda2, currentState.lambda2, "TZINOR_WINDOW");
            } else if (currentState.lambda2 <= TAU_CRITICAL_KURAMOTO && previousLambda2 > TAU_CRITICAL_KURAMOTO) {
                emit PhaseTransition(block.number, previousLambda2, currentState.lambda2, "DECOHERENCE");
            }
        }
    }

    function _computeOrderParameter() internal view returns (uint256 r, int256 psi) {
        // Simulação do cálculo do parâmetro de ordem
        // r = |1/N * sum(exp(i*theta_i))|
        int256 sumSin = 0;
        int256 sumCos = 0;
        for (uint256 i = 0; i < OSCILLATOR_COUNT; i++) {
            sumSin += _sin(currentPhases[i]);
            sumCos += _cos(currentPhases[i]);
        }

        r = uint256(sqrt(uint256((sumSin*sumSin + sumCos*sumCos) / int256(OSCILLATOR_COUNT * OSCILLATOR_COUNT))));
        psi = _atan2(sumSin, sumCos);
    }

    // Funções auxiliares matemáticas simplificadas
    function _sin(int256 _a) internal pure returns (int256) {
        return _a % 1000; // Mock
    }

    function _cos(int256 _a) internal pure returns (int256) {
        return 1000 - (_a % 1000); // Mock
    }

    function _wrapPhase(int256 _a) internal pure returns (int256) {
        return _a % 6283; // 2 * PI * 1000
    }

    function _atan2(int256 y, int256 x) internal pure returns (int256) {
        if (x == 0) return 0;
        return (y / x) * 1000; // Mock
    }

    function sqrt(uint256 x) internal pure returns (uint256 y) {
        uint256 z = (x + 1) / 2;
        y = x;
        while (z < y) {
            y = z;
            z = (x / z + z) / 2;
        }
    }
}
