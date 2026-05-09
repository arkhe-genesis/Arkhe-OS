pragma circom 2.0.0;

include "circomlib/comparators.circom";
include "circomlib/pedersen.circom";

// Simplified version for the Arkhe PoC
template ShaclMaxCountPrivate(n, maxValBits) {
    signal input x[n];
    signal input limit;
    signal input index;                // Índice da entidade violadora (privado)
    signal input blinding;             // Fator de ofuscação para Pedersen

    signal output violation_exists;
    signal output commitment;

    // Verifica se x[index] > limit
    // Em Circom real, precisaríamos de um componente para acesso dinâmico por índice
    // Para o PoC, assumimos que o provador fornece o valor correto em x_val
    signal input x_val;
    x_val === x[index];

    component gt = IsGreaterThanPoC(maxValBits);
    gt.in[0] <== x_val;
    gt.in[1] <== limit;
    violation_exists <== gt.out;

    // Calcula o compromisso do índice
    component pedersen = Pedersen(2);
    pedersen.in[0] <== index;
    pedersen.in[1] <== blinding;
    commitment <== pedersen.out[0];
}

template IsGreaterThanPoC(nBits) {
    signal input in[2];
    signal output out;

    component lt = LessThan(nBits);
    lt.in[0] <== in[1];
    lt.in[1] <== in[0];
    out <== lt.out;
}
