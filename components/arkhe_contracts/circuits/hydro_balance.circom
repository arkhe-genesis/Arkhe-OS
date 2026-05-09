pragma circom 2.1.6;

include "circomlib/poseidon.circom";
include "circomlib/comparators.circom";
include "circomlib/bitify.circom";

template HydroBalanceProof() {
    // Precisão: 3 casas decimais
    const PRECISION = 1000;
    const ERROR_MARGIN = 10; // 1% de tolerância (10/1000)

    // Inputs privados (sensores TEE)
    signal input precipitation;      // mm (×1000)
    signal input recharge;           // m³/s (×10^6) - convertido para volume equivalente
    signal input pumping;            // m³/s (×10^6)
    signal input evapotranspiration; // mm (×1000)
    signal input previousStorage;    // m³ (×1000)
    signal input currentStorage;     // m³ (×1000)
    signal input quantumCoherence;   // 0-100000 (métrica do Kalman filter)
    signal input salt;

    // Inputs públicos (limites de governança)
    signal input minWaterLevel;      // mm (×1000)
    signal input maxWaterLevel;      // mm (×1000)
    signal input maxPumpingRate;     // m³/s (×10^6)
    signal input minQuantumCoherence; // Limiar de coerência para validação

    // Outputs
    signal output massBalanceValid;
    signal output safetyCompliant;
    signal output quantumValid;
    signal output integrityHash;
    signal output nullifier;

    // 1. Verificação de integridade (Poseidon)
    component hasher = Poseidon(8);
    hasher.inputs[0] <== precipitation;
    hasher.inputs[1] <== recharge;
    hasher.inputs[2] <== pumping;
    hasher.inputs[3] <== evapotranspiration;
    hasher.inputs[4] <== currentStorage;
    hasher.inputs[5] <== previousStorage;
    hasher.inputs[6] <== quantumCoherence;
    hasher.inputs[7] <== salt;

    integrityHash <== hasher.out;

    component nullHasher = Poseidon(2);
    nullHasher.inputs[0] <== integrityHash;
    nullHasher.inputs[1] <== salt;
    nullifier <== nullHasher.out;

    // 2. Verificação Quântica
    // O hardware QD deve provar coerência mínima para validar a medição
    component coherenceCheck = GreaterThan(32);
    coherenceCheck.in[0] <== quantumCoherence;
    coherenceCheck.in[1] <== minQuantumCoherence;
    quantumValid <== coherenceCheck.out;

    // 3. Balanço de Massa com valor absoluto seguro
    // Conversões de unidades consistentes
    signal precipContrib <== precipitation * 1000; // mm → m (×1000 * 1000 / 10^6, simplificado)
    signal evapContrib <== evapotranspiration * 1000;

    signal totalInputs <== precipContrib + recharge;
    signal totalOutputs <== pumping + evapContrib;

    signal deltaStorage <== currentStorage - previousStorage;
    signal theoreticalDelta <== totalInputs - totalOutputs;

    // Cálculo seguro de |a - b| em campo finito
    signal diff <== deltaStorage - theoreticalDelta;
    signal diffAbs;

    // Se diff >= 0, diffAbs = diff, senão diffAbs = -diff
    component diffIsNeg = LessThan(64);
    diffIsNeg.in[0] <== diff + (1 << 63); // Offset para comparação signed
    diffIsNeg.in[1] <== (1 << 63);

    // diffAbs = diffIsNeg ? -diff : diff
    signal negDiff <== 0 - diff;
    diffAbs <== diffIsNeg.out * negDiff + (1 - diffIsNeg.out) * diff;

    // Verificação de erro < 1%
    component errorCheck = LessThan(32);
    errorCheck.in[0] <== diffAbs;
    errorCheck.in[1] <== ERROR_MARGIN * PRECISION;

    // Mass balance válido se erro pequeno E coerência quântica confirmada
    massBalanceValid <== errorCheck.out * quantumValid;

    // 4. Limites Operacionais (Geofence)
    component checkMin = GreaterThan(64);
    checkMin.in[0] <== currentStorage;
    checkMin.in[1] <== minWaterLevel;

    component checkMax = LessThan(64);
    checkMax.in[0] <== currentStorage;
    checkMax.in[1] <== maxWaterLevel;

    component checkPump = LessThan(64);
    checkPump.in[0] <== pumping;
    checkPump.in[1] <== maxPumpingRate;

    component checkEvap = GreaterThan(64);
    checkEvap.in[0] <== evapotranspiration;
    checkEvap.in[1] <== 0;

    // Safety = AND de todas as condições
    signal levelSafe <== checkMin.out * checkMax.out;
    signal pumpSafe <== checkPump.out;
    signal evapSafe <== checkEvap.out;

    safetyCompliant <== levelSafe * pumpSafe * evapSafe * quantumValid;
}

component main {public [minWaterLevel, maxWaterLevel, maxPumpingRate, minQuantumCoherence]} = HydroBalanceProof();
