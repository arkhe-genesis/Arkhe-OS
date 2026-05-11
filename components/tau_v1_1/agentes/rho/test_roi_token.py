import pytest
from roi_token import ROIToken

def test_roi_token_from_bytes():
    # Little-endian:
    # Bytes 0-1: X=0xABCD -> CD AB
    # Bytes 2-3: Y=0x1234 -> 34 12
    # Bytes 4-5: Z=0x5678 -> 78 56
    # Byte 6: Intensity MSB = 0xFF
    # Byte 7: Flags = 0x0F (all bits set: red, green, blue, high_intensity)
    data = b'\xCD\xAB\x34\x12\x78\x56\xFF\x0F'
    token = ROIToken.from_bytes(data)

    assert token.x == 0xABCD
    assert token.y == 0x1234
    assert token.z == 0x5678
    assert token.intensity_msb == 0xFF
    assert token.is_red is True
    assert token.is_green is True
    assert token.is_blue is True
    assert token.is_high_intensity is True

def test_roi_token_to_bytes():
    token = ROIToken(
        x=0xABCD, y=0x1234, z=0x5678,
        is_red=True, is_green=False, is_blue=True, is_high_intensity=False,
        intensity_msb=0x80
    )
    # Expected: CD AB 34 12 78 56 80 05 (0x01 | 0x04)
    expected = b'\xCD\xAB\x34\x12\x78\x56\x80\x05'
    assert token.to_bytes() == expected

def test_roi_token_roundtrip():
    original = ROIToken(
        x=123, y=456, z=789,
        is_red=False, is_green=True, is_blue=False, is_high_intensity=True,
        intensity_msb=128
    )
    data = original.to_bytes()
    decoded = ROIToken.from_bytes(data)
    assert original == decoded

def test_invalid_length():
    with pytest.raises(ValueError):
        ROIToken.from_bytes(b'\x00' * 7)
    with pytest.raises(ValueError):
        ROIToken.from_bytes(b'\x00' * 9)
