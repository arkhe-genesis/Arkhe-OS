import sys
import numpy as np

def test_gluing_kernel():
    from core.gluing_kernel import gluing_kernel_tanh, get_gluing_kernel, GLUING_KERNEL_PARAMS

    # Test the empirical get_gluing_kernel function
    kernel_default = get_gluing_kernel('default')
    assert callable(kernel_default)

    # Evaluate at bounds and center
    t = np.linspace(0, 1, 101)  # 101 points so that t=0.5 is exactly at index 50
    sigma = kernel_default(t)

    assert np.isclose(sigma[50], 0.5)

    # Test different profiles have different steepness
    kernel_sharp = get_gluing_kernel('sharp_transition')
    sigma_sharp = kernel_sharp(t)

    # Sharp transition should change faster near center
    diff_sharp = sigma_sharp[55] - sigma_sharp[45]
    diff_default = sigma[55] - sigma[45]
    assert diff_sharp > diff_default

if __name__ == '__main__':
    test_gluing_kernel()
    print("Tests passed.")
