pragma circom 2.1.6;

include "circomlib/poseidon.circom";
include "circomlib/comparators.circom";
include "circomlib/bitify.circom";

template HydroBalanceProof() {
    const PRECISION = 1000;
    const ERROR_MARGIN = 10; // 1%

    // === INPUTS PRIVADOS ===
    signal input precipitation;      // mm (×1000)
    signal input recharge;           // m³/s (×10^6)
    signal input pumping;            // m³/s (×10^6)
    signal input evapotranspiration; // mm (×1000)
    signal input previousStorage;    // m³ (×1000)
    signal input currentStorage;     // m³ (×1000)
    signal input quantumCoherence;   // 0-100000 (do Kalman filter)
    signal input salt;

    // === INPUTS PÚBLICOS ===
    signal input minWaterLevel;      // mm (×1000)
    signal input maxWaterLevel;      // mm (×1000)
    signal input maxPumpingRate;     // m³/s (×10^6)
    signal input minQuantumCoherence; // Limiar T2*

    // === OUTPUTS ===
    signal output massBalanceValid;
    signal output safetyCompliant;
    signal output quantumValid;
    signal output integrityHash;
    signal output nullifier;

    // 1. Integridade (Poseidon-8)
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

    // 2. Verificação Quântica (O hardware testemunha a coerência)
    component coherenceCheck = GreaterThan(32);
    coherenceCheck.in[0] <== quantumCoherence;
    coherenceCheck.in[1] <== minQuantumCoherence;
    quantumValid <== coherenceCheck.out;

    // 3. Balanço de Massa com |x| seguro em campo finito
    // Conversões: tudo para mm-equivalente-volume
    signal precipContrib <== precipitation * 1000;
    signal evapContrib <== evapotranspiration * 1000;

    signal totalInputs <== precipContrib + recharge;
    signal totalOutputs <== pumping + evapContrib;

    signal deltaStorage <== currentStorage - previousStorage;
    signal theoreticalDelta <== totalInputs - totalOutputs;

    // |a - b| sem underflow: compara antes de subtrair
    signal diff <== deltaStorage - theoreticalDelta;
    signal diffAbs;

    // Verifica se diff é negativo (em complemento de 2)
    component diffIsNeg = LessThan(64);
    diffIsNeg.in[0] <== diff + (1 << 63); // Offset para signed
    diffIsNeg.in[1] <== (1 << 63);

    // diffAbs = diff >= 0 ? diff : -diff
    signal negDiff <== 0 - diff;
    diffAbs <== diffIsNeg.out * negDiff + (1 - diffIsNeg.out) * diff;

    // Erro < 1% ?
    component errorCheck = LessThan(32);
    errorCheck.in[0] <== diffAbs;
    errorCheck.in[1] <== ERROR_MARGIN * PRECISION;

    // Mass balance válido SOMENTE se quanticamente coerente
    massBalanceValid <== errorCheck.out * quantumValid;

    // 4. Geofence (Limites Operacionais)
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

    signal levelSafe <== checkMin.out * checkMax.out;
    signal pumpSafe <== checkPump.out;
    signal evapSafe <== checkEvap.out;

    // Safety só é válido se tudo for verdadeiro E o quantum for coerente
    safetyCompliant <== levelSafe * pumpSafe * evapSafe * quantumValid;
}

component main {public [minWaterLevel, maxWaterLevel, maxPumpingRate, minQuantumCoherence]} = HydroBalanceProof();
