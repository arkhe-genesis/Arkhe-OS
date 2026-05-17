import pytest
import random
from substrates.substrato_205_3_1_toom import ToomCook

def test_toom_6():
    a = random.getrandbits(1024)
    b = random.getrandbits(1024)
    assert ToomCook.toom_nh_mul(a, b, k=6) == a * b

def test_toom_8():
    a = random.getrandbits(1024)
    b = random.getrandbits(1024)
    assert ToomCook.toom_nh_mul(a, b, k=8) == a * b

def test_unsupported_k():
    with pytest.raises(ValueError):
        ToomCook.toom_nh_mul(10, 10, k=4)

def test_schonhage_strassen_fft_mul():
    a = random.getrandbits(1024)
    b = random.getrandbits(1024)
    assert ToomCook.schonhage_strassen_fft_mul(a, b, limb_bits=64) == a * b

def test_toom63_mul():
    a = random.getrandbits(1024)
    b = random.getrandbits(512)
    assert ToomCook.toom63_mul(a, b, limb_bits=64) == a * b

def test_toom52_mul():
    a = random.getrandbits(1024)
    b = random.getrandbits(400)
    assert ToomCook.toom52_mul(a, b, limb_bits=64) == a * b

def test_toom_even_odd_mul():
    a = random.getrandbits(1024)
    b = random.getrandbits(1024)
    assert ToomCook.toom_even_odd_mul(a, b, k=6, limb_bits=64) == a * b
    assert ToomCook.toom_even_odd_mul(a, b, k=8, limb_bits=64) == a * b

def test_avx512_ifma_mul():
    a = random.getrandbits(2048)
    b = random.getrandbits(2048)
    assert ToomCook.avx512_ifma_mul(a, b) == a * b

def test_mul_fft_threshold_trigger():
    # Simulate a case where limbs exceed the MUL_FFT_THRESHOLD
    # MUL_FFT_THRESHOLD is 1024 limbs of 64 bits = 65536 bits
    # Let's mock the bit length instead of generating a massive integer which might take a long time to multiply.

    # We will test the threshold dispatch specifically by mocking
    original_threshold = ToomCook.MUL_FFT_THRESHOLD
    ToomCook.MUL_FFT_THRESHOLD = 10

    a = random.getrandbits(64 * 12)
    b = random.getrandbits(64 * 12)
    # The multiplication should use Schonhage-Strassen due to dispatch
    assert ToomCook.toom_nh_mul(a, b, k=6) == a * b

    ToomCook.MUL_FFT_THRESHOLD = original_threshold
