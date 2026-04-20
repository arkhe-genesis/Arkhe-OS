pragma circom 2.0.0;

include "circomlib/bitify.circom";
include "circomlib/comparators.circom";

template ShaclMaxCountViolation(n, maxValBits) {
    // n: número de entidades sob análise
    // maxValBits: número de bits para representar x_i e N_max (ex: 32 bits)

    signal input x[n];                 // Valores de contagem (privados)
    signal input limit;                // Limite N_max (público)
    signal output violation_exists;    // 1 se existe violação, 0 caso contrário

    component violations[n];
    signal total;

    var v_sum = 0;
    for (var i = 0; i < n; i++) {
        violations[i] = IsGreaterThan(maxValBits);
        violations[i].in[0] <== x[i];
        violations[i].in[1] <== limit;
        v_sum += violations[i].out;
    }

    total <== v_sum;

    // Verifica se total > 0
    component isNonZero = IsZero();
    isNonZero.in <== total;
    violation_exists <== 1 - isNonZero.out;
}

template IsGreaterThan(nBits) {
    signal input in[2];
    signal output out;

    // out = 1 se in[0] > in[1]
    component lt = LessThan(nBits);
    lt.in[0] <== in[1];
    lt.in[1] <== in[0];
    out <== lt.out;
}
