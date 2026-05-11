# core/cbytes_compiler.py — Keccak256 corrigido e Yul Gen
from Crypto.Hash import keccak

def keccak256(data: bytes) -> bytes:
    """Keccak-256 hash com pycryptodome, compatível com EVM."""
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()

def _run_keccak_tests():
    assert keccak256(b"") == bytes.fromhex(
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    ), "Empty string hash mismatch"
    assert keccak256(b"ARKHE") == bytes.fromhex(
        "38bb76228f8f74b7c07a9871a6f1784c8ca3fa396e191d1571b13199be112ec1"
    )[:64], "Sanity check"  # Truncado para exemplo
    return True

if not _run_keccak_tests():
    raise RuntimeError("Keccak256 self-tests failed")


def memory_expansion_cost(current_mem_words: int, offset: int, length: int) -> int:
    """Calcula custo de expansão de memória conforme EIP-150."""
    if length == 0:
        return 0

    required_words = (offset + length + 31) // 32
    if required_words <= current_mem_words:
        return 0

    def mem_cost(words: int) -> int:
        return 3 * words + (words * words) // 512

    return mem_cost(required_words) - mem_cost(current_mem_words)

class BytecodeEncoder:
    PUSH_OPCODES = {i: 0x5f + i for i in range(1, 33)}  # PUSH1..PUSH32

    def encode_push(self, value: int, width: int) -> bytes:
        if not (1 <= width <= 32):
            raise ValueError(f"PUSH width must be 1-32, got {width}")

        max_val = (1 << (8 * width)) - 1
        if value < 0 or value > max_val:
            raise ValueError(
                f"Value {value} out of range for PUSH{width} (max: {max_val})"
            )

        operand = value.to_bytes(width, byteorder='big')
        return bytes([self.PUSH_OPCODES[width]]) + operand

    def generate_yul(self) -> str:
        return """
object "ARKHECBytes" {
    code {
        datacopy(0, dataoffset("runtime"), datasize("runtime"))
        return(0, datasize("runtime"))
    }

    object "runtime" {
        code {
            if lt(calldatasize(), 36) { revert(0, 0) }
            let selector := shr(224, calldataload(0))
            if eq(selector, 0x9c3e6e8e) {
                let argOffset := 4
                let argLength := calldataload(argOffset)
                if gt(argLength, 0xffff) { revert(0, 0) }

                let freePtr := mload(0x40)
                let requiredSize := add(argLength, 32)
                mstore(0x40, add(freePtr, requiredSize))

                codecopy(freePtr, add(argOffset, 32), argLength)
                let hash := keccak256(freePtr, argLength)

                mstore(freePtr, hash)
                return(freePtr, 32)
            }
            revert(0, 0)
        }
    }
}
        """
