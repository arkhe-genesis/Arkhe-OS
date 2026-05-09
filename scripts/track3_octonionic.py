import numpy as np

def oct_multiply(A, B):
    """
    Multiplicação octoniônica ponto a ponto.
    A, B: arrays de shape (8, Ny, Nx) representando componentes e0..e7
    Retorna: A * B (shape 8, Ny, Nx)
    """
    R = np.zeros_like(A)
    R[0] = A[0]*B[0] - np.sum(A[1:]*B[1:], axis=0)
    R[1] = A[0]*B[1] + A[1]*B[0] - A[2]*B[3] - A[3]*B[2] - A[4]*B[5] - A[5]*B[4] + A[6]*B[7] + A[7]*B[6]
    R[2] = A[0]*B[2] + A[1]*B[3] + A[2]*B[0] - A[3]*B[1] - A[4]*B[6] - A[5]*B[7] - A[6]*B[4] + A[7]*B[5]
    R[3] = A[0]*B[3] - A[1]*B[2] + A[2]*B[1] + A[3]*B[0] - A[4]*B[7] + A[5]*B[6] + A[6]*B[5] - A[7]*B[4]
    R[4] = A[0]*B[4] + A[1]*B[5] + A[2]*B[6] + A[3]*B[7] + A[4]*B[0] - A[5]*B[1] + A[6]*B[2] - A[7]*B[3]
    R[5] = A[0]*B[5] - A[1]*B[4] + A[2]*B[7] - A[3]*B[6] + A[4]*B[1] + A[5]*B[0] - A[6]*B[3] + A[7]*B[2]
    R[6] = A[0]*B[6] + A[1]*B[7] - A[2]*B[4] - A[3]*B[5] - A[4]*B[2] + A[5]*B[3] + A[6]*B[0] + A[7]*B[1]
    R[7] = A[0]*B[7] - A[1]*B[6] + A[2]*B[5] - A[3]*B[4] + A[4]*B[3] - A[5]*B[2] - A[6]*B[1] + A[7]*B[0]
    return R

def compute_octonionic_associator_norm(u_field, v_field, p_field):
    """
    Calcula a norma L² do associador octoniônico nos campos de velocidade/pressão.
    Mapeia: e1=u, e2=v, e3=∇·u (deve ser ~0), e4=p, e5..e7=0 (embedding mínimo)
    Retorna: ||[A,B,C]||_L2 (escalar global)
    """
    def embed(U, V, P):
        E = np.zeros((8, *U.shape))
        E[0] = np.zeros_like(U)
        E[1] = U; E[2] = V
        E[3] = np.zeros_like(U)
        E[4] = P
        return E

    A = embed(u_field, v_field, p_field)
    B = np.roll(A, shift=2, axis=(1,2))
    C = np.roll(A, shift=-3, axis=(1,2))

    AB = oct_multiply(A, B)
    ABC_left = oct_multiply(AB, C)
    BC = oct_multiply(B, C)
    ABC_right = oct_multiply(A, BC)

    associator_field = ABC_left - ABC_right
    norm_L2 = np.sqrt(np.mean(np.sum(associator_field**2, axis=0)))
    return float(norm_L2)
