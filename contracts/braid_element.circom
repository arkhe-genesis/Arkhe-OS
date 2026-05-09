pragma circom 2.0.0;

// ARKHE OS v_inf.Omega.1.1 -- Braid Element Verification Circuit
// Verifica que uma matriz 2x2 complexa eh um elemento valido de B3
// na representacao de Jones com q = e^(i*pi/5)

template ComplexMul() {
    signal input a_re, a_im, b_re, b_im;
    signal output c_re, c_im;

    c_re <== a_re * b_re - a_im * b_im;
    c_im <== a_re * b_im + a_im * b_re;
}

template UnitarityCheck() {
    // Verifica M_dagger * M = I para matriz 2x2 complexa
    signal input m_re[2][2], m_im[2][2];

    // M_dagger * M = I implica:
    // |m_00|^2 + |m_10|^2 = 1
    // |m_01|^2 + |m_11|^2 = 1
    // m_00* * m_01 + m_10* * m_11 = 0

    signal m00_sq <== m_re[0][0] * m_re[0][0] + m_im[0][0] * m_im[0][0];
    signal m10_sq <== m_re[1][0] * m_re[1][0] + m_im[1][0] * m_im[1][0];
    signal m01_sq <== m_re[0][1] * m_re[0][1] + m_im[0][1] * m_im[0][1];
    signal m11_sq <== m_re[1][1] * m_re[1][1] + m_im[1][1] * m_im[1][1];

    // Coluna 0 normalizada
    m00_sq + m10_sq === 1;

    // Coluna 1 normalizada
    m01_sq + m11_sq === 1;

    // Ortogonalidade das colunas (parte real e imaginaria)
    signal orth_re <== m_re[0][0] * m_re[0][1] + m_im[0][0] * m_im[0][1]
                     + m_re[1][0] * m_re[1][1] + m_im[1][0] * m_im[1][1];
    signal orth_im <== -m_im[0][0] * m_re[0][1] + m_re[0][0] * m_im[0][1]
                      -m_im[1][0] * m_re[1][1] + m_re[1][0] * m_im[1][1];

    orth_re === 0;
    orth_im === 0;
}

template BraidElementVerification() {
    signal input m_re[2][2], m_im[2][2];

    component unitary = UnitarityCheck();
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            unitary.m_re[i][j] <== m_re[i][j];
            unitary.m_im[i][j] <== m_im[i][j];
        }
    }

    // NOTA: Verificar pertencimento a B3 (fecho de {sigma1, sigma2})
    // eh computacionalmente dificil em ZK. Alternativas:
    // 1. Verificar que M satisfaz a relacao de tranca com matrizes conhecidas
    // 2. Prover fornece decomposicao em geradores + verificacao passo-a-passo
    // 3. Usar accumulator para produto de geradores verificaveis
}

component main = BraidElementVerification();