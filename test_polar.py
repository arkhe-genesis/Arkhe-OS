import numpy as np

N = 8
G2 = np.array([[1, 0], [1, 1]])
G = G2
for _ in range(int(np.log2(N)) - 1):
    G = np.kron(G, G2)

u = np.array([0, 1, 0, 0, 1, 1, 0, 1])
res1 = (u @ G) % 2

x = u.copy()
n = int(np.log2(N))
for stage in range(n):
    stride = 1 << stage
    for i in range(0, N, 2 * stride):
        for j in range(stride):
            x[i + j] = (x[i + j] + x[i + j + stride]) % 2
res2 = x

print("res1:", res1)
print("res2:", res2)
print("Match?", np.array_equal(res1, res2))
