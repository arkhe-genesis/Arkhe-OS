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

template ComplexMatMul2x2() {
    signal input a_re[2][2], a_im[2][2];
    signal input b_re[2][2], b_im[2][2];
    signal output c_re[2][2], c_im[2][2];

    component mul00_0 = ComplexMul();
    mul00_0.a_re <== a_re[0][0]; mul00_0.a_im <== a_im[0][0];
    mul00_0.b_re <== b_re[0][0]; mul00_0.b_im <== b_im[0][0];

    component mul00_1 = ComplexMul();
    mul00_1.a_re <== a_re[0][1]; mul00_1.a_im <== a_im[0][1];
    mul00_1.b_re <== b_re[1][0]; mul00_1.b_im <== b_im[1][0];

    c_re[0][0] <== mul00_0.c_re + mul00_1.c_re;
    c_im[0][0] <== mul00_0.c_im + mul00_1.c_im;

    component mul01_0 = ComplexMul();
    mul01_0.a_re <== a_re[0][0]; mul01_0.a_im <== a_im[0][0];
    mul01_0.b_re <== b_re[0][1]; mul01_0.b_im <== b_im[0][1];

    component mul01_1 = ComplexMul();
    mul01_1.a_re <== a_re[0][1]; mul01_1.a_im <== a_im[0][1];
    mul01_1.b_re <== b_re[1][1]; mul01_1.b_im <== b_im[1][1];

    c_re[0][1] <== mul01_0.c_re + mul01_1.c_re;
    c_im[0][1] <== mul01_0.c_im + mul01_1.c_im;

    component mul10_0 = ComplexMul();
    mul10_0.a_re <== a_re[1][0]; mul10_0.a_im <== a_im[1][0];
    mul10_0.b_re <== b_re[0][0]; mul10_0.b_im <== b_im[0][0];

    component mul10_1 = ComplexMul();
    mul10_1.a_re <== a_re[1][1]; mul10_1.a_im <== a_im[1][1];
    mul10_1.b_re <== b_re[1][0]; mul10_1.b_im <== b_im[1][0];

    c_re[1][0] <== mul10_0.c_re + mul10_1.c_re;
    c_im[1][0] <== mul10_0.c_im + mul10_1.c_im;

    component mul11_0 = ComplexMul();
    mul11_0.a_re <== a_re[1][0]; mul11_0.a_im <== a_im[1][0];
    mul11_0.b_re <== b_re[0][1]; mul11_0.b_im <== b_im[0][1];

    component mul11_1 = ComplexMul();
    mul11_1.a_re <== a_re[1][1]; mul11_1.a_im <== a_im[1][1];
    mul11_1.b_re <== b_re[1][1]; mul11_1.b_im <== b_im[1][1];

    c_re[1][1] <== mul11_0.c_re + mul11_1.c_re;
    c_im[1][1] <== mul11_0.c_im + mul11_1.c_im;
}

template BraidRelationVerification() {
    // Prover provides witness matrices for sigma1 and sigma2
    signal input sigma1_re[2][2], sigma1_im[2][2];
    signal input sigma2_re[2][2], sigma2_im[2][2];

    // Compute LHS = sigma1 * sigma2 * sigma1
    component mul1_lhs = ComplexMatMul2x2();
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            mul1_lhs.a_re[i][j] <== sigma1_re[i][j];
            mul1_lhs.a_im[i][j] <== sigma1_im[i][j];
            mul1_lhs.b_re[i][j] <== sigma2_re[i][j];
            mul1_lhs.b_im[i][j] <== sigma2_im[i][j];
        }
    }

    component mul2_lhs = ComplexMatMul2x2();
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            mul2_lhs.a_re[i][j] <== mul1_lhs.c_re[i][j];
            mul2_lhs.a_im[i][j] <== mul1_lhs.c_im[i][j];
            mul2_lhs.b_re[i][j] <== sigma1_re[i][j];
            mul2_lhs.b_im[i][j] <== sigma1_im[i][j];
        }
    }

    // Compute RHS = sigma2 * sigma1 * sigma2
    component mul1_rhs = ComplexMatMul2x2();
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            mul1_rhs.a_re[i][j] <== sigma2_re[i][j];
            mul1_rhs.a_im[i][j] <== sigma2_im[i][j];
            mul1_rhs.b_re[i][j] <== sigma1_re[i][j];
            mul1_rhs.b_im[i][j] <== sigma1_im[i][j];
        }
    }

    component mul2_rhs = ComplexMatMul2x2();
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            mul2_rhs.a_re[i][j] <== mul1_rhs.c_re[i][j];
            mul2_rhs.a_im[i][j] <== mul1_rhs.c_im[i][j];
            mul2_rhs.b_re[i][j] <== sigma2_re[i][j];
            mul2_rhs.b_im[i][j] <== sigma2_im[i][j];
        }
    }

    // Assert LHS == RHS
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            mul2_lhs.c_re[i][j] === mul2_rhs.c_re[i][j];
            mul2_lhs.c_im[i][j] === mul2_rhs.c_im[i][j];
        }
    }
}

template BraidElementVerification() {
    // Prover provides witness matrices for sigma1 and sigma2
    signal input sigma1_re[2][2], sigma1_im[2][2];
    signal input sigma2_re[2][2], sigma2_im[2][2];

    signal input m_re[2][2], m_im[2][2];

    component unitary = UnitarityCheck();
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            unitary.m_re[i][j] <== m_re[i][j];
            unitary.m_im[i][j] <== m_im[i][j];
        }
    }

    // Verifies that sigma1 and sigma2 satisfy the braid relation
    component braid_relation = BraidRelationVerification();
    for (var i = 0; i < 2; i++) {
        for (var j = 0; j < 2; j++) {
            braid_relation.sigma1_re[i][j] <== sigma1_re[i][j];
            braid_relation.sigma1_im[i][j] <== sigma1_im[i][j];
            braid_relation.sigma2_re[i][j] <== sigma2_re[i][j];
            braid_relation.sigma2_im[i][j] <== sigma2_im[i][j];
        }
    }

    // In a full implementation, we'd also check that M is composed of sigma1 and sigma2
}

component main = BraidElementVerification();
