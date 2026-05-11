import struct
from dataclasses import dataclass

@dataclass
class ROIToken:
    x: int
    y: int
    z: int
    is_red: bool
    is_green: bool
    is_blue: bool
    is_high_intensity: bool
    intensity_msb: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "ROIToken":
        if len(data) != 8:
            raise ValueError(f"ROIToken requer 8 bytes, recebido {len(data)}")

        # Layout little-endian (bytes):
        # 0-1: x (uint16), 2-3: y (uint16), 4-5: z (uint16), 6: intensity_msb, 7: flags
        x, y, z, intensity_msb, flags = struct.unpack('<HHHBB', data)

        return cls(
            x=x,
            y=y,
            z=z,
            is_red=bool(flags & 0x01),
            is_green=bool(flags & 0x02),
            is_blue=bool(flags & 0x04),
            is_high_intensity=bool(flags & 0x08),
            intensity_msb=intensity_msb
        )

    def to_bytes(self) -> bytes:
        flags = (
            (0x01 if self.is_red else 0) |
            (0x02 if self.is_green else 0) |
            (0x04 if self.is_blue else 0) |
            (0x08 if self.is_high_intensity else 0)
        )
        return struct.pack('<HHHBB', self.x, self.y, self.z, self.intensity_msb, flags)

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "flags": {
                "red": self.is_red,
                "green": self.is_green,
                "blue": self.is_blue,
                "high_intensity": self.is_high_intensity
            },
            "intensity_msb": self.intensity_msb
        }
