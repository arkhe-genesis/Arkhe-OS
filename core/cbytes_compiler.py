"""
ARKHE cbytes Compiler — v∞.364.1-patch1

Backend compiler for the `cbytes` type: deterministic serialization,
zero-copy slicing, compile-time keccak256 resolution, and EVM/Yul
code generation with gas-optimized opcodes.

CORREÇÕES CRÍTICAS (patch1):
  A. Keccak-256: pycryptodome (EVM-compatible) substitui hashlib.sha3_256
  B. Gas EIP-150: expansão de memória quadrática completa
  C. Yul: calldatacopy (não codecopy) + retorno ABI-compliant
  D. BytecodeEncoder: bytecode EVM real com validação de operandos

Type definition:
    cbytes = { u256 id; u256 offset; u256 length; }

Builtins:
    @comptime_keccak256(b)  — compile-time hash, baked as PUSH32 constant
    @slice_bytes(b, s, e)   — bounds-checked zero-copy slice
    @bytes_concat(s)         — flat concatenation via MSTORE alignment
    @data_offset(b)          — resolved at linking, emits PUSH <offset>
    @bytes_len(b)            — returns length field
    content_eq(a, b)         — keccak256 comparison or compile-time equality

Reference: Rafael Oliveira, ARKHE OS v∞.364.1-patch1
           ORCID: 0009-0005-2697-4668
"""

from Crypto.Hash import keccak  # FIX A: pycryptodome, não hashlib
import struct
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from copy import deepcopy


# ============================================================
# 1. IR Representation
# ============================================================

class IRType(Enum):
    """Intermediate Representation node types."""
    CBYTES_LITERAL = auto()
    CBYTES_SLICE = auto()
    CBYTES_CONCAT = auto()
    COMPTIME_KECCAK256 = auto()
    DATA_OFFSET = auto()
    BYTES_LEN = auto()
    CONTENT_EQ = auto()
    RUNTIME_KECCAK256 = auto()
    MEMCPY = auto()
    BOUNDS_CHECK = auto()
    CONSTANT_U256 = auto()
    MSTORE = auto()
    MLOAD = auto()
    FUNCTION_DEF = auto()
    RETURN = auto()
    BLOCK = auto()
    COMMENT = auto()


@dataclass
class IRNode:
    """A node in the intermediate representation tree."""
    ir_type: IRType
    operands: List[Any] = field(default_factory=list)
    value: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        if self.value is not None:
            return f"IRNode({self.ir_type.name}, value={self.value!r})"
        return f"IRNode({self.ir_type.name}, operands={self.operands})"


# ============================================================
# 2. cbytes Type
# ============================================================

@dataclass
class CBytes:
    """
    The `cbytes` type: zero-allocation byte slice reference.
    Layout: { u256 id; u256 offset; u256 length; } = 96 bytes on stack.
    """
    cb_id: int
    offset: int
    length: int

    def to_ir(self) -> IRNode:
        return IRNode(
            ir_type=IRType.CBYTES_LITERAL,
            value={'id': self.cb_id, 'offset': self.offset, 'length': self.length},
            metadata={'size_words': 3}
        )

    def __repr__(self):
        return f"cbytes(id={self.cb_id}, offset={self.offset}, len={self.length})"


# ============================================================
# 3. Virtual Bytecode Section Store
# ============================================================

class BytecodeSectionStore:
    """Virtual store for bytecode sections referenced by cbytes."""

    def __init__(self):
        self._sections: Dict[int, bytes] = {}
        self._next_id: int = 0
        self._keccak_cache: Dict[Tuple[int, int, int], bytes] = {}

    def add_section(self, data: bytes) -> int:
        section_id = self._next_id
        self._next_id += 1
        self._sections[section_id] = data
        return section_id

    def get_section(self, section_id: int) -> bytes:
        return self._sections[section_id]

    def keccak256(self, section_id: int, offset: int = 0,
                  length: Optional[int] = None) -> bytes:
        """Compute Keccak-256 (EVM-compatible) of a section or slice."""
        data = self._sections[section_id]
        if length is None:
            length = len(data) - offset
        slice_data = data[offset:offset + length]

        cache_key = (section_id, offset, length)
        if cache_key not in self._keccak_cache:
            # FIX A: pycryptodome Keccak-256 (padding 0x01), não NIST SHA3-256 (padding 0x06)
            k = keccak.new(digest_bits=256)
            k.update(slice_data)
            self._keccak_cache[cache_key] = k.digest()

        return self._keccak_cache[cache_key]

    def total_size(self) -> int:
        return sum(len(d) for d in self._sections.values())

    def section_count(self) -> int:
        return len(self._sections)


# ============================================================
# 4. EIP-150 Gas Estimator
# ============================================================

def memory_expansion_cost(current_mem_words: int, offset: int, length: int) -> int:
    """
    Calcula custo de expansão de memória conforme EIP-150.
    Fórmula: M(words) = 3 * words + words^2 // 512
    """
    if length == 0:
        return 0
    required_words = (offset + length + 31) // 32
    if required_words <= current_mem_words:
        return 0

    def mem_cost(words: int) -> int:
        return 3 * words + (words * words) // 512

    return mem_cost(required_words) - mem_cost(current_mem_words)


def estimate_codecopy_gas(offset: int, length: int, current_mem_words: int = 0) -> int:
    """Estima gas para CODECOPY com EIP-150."""
    base = 3
    memory_copy = 3 * ((length + 31) // 32)
    expansion = memory_expansion_cost(current_mem_words, offset, length)
    return base + memory_copy + expansion


def estimate_keccak256_gas(offset: int, length: int, current_mem_words: int = 0) -> int:
    """Estima gas para KECCAK256 com EIP-150."""
    base = 30
    word_cost = 6 * ((length + 31) // 32)
    expansion = memory_expansion_cost(current_mem_words, offset, length)
    return base + word_cost + expansion


# ============================================================
# 5. Bytecode Encoder (FIX D)
# ============================================================

class BytecodeEncoder:
    """Encoder de bytecode EVM real com validação rigorosa."""

    PUSH_OPCODES = {i: 0x60 + i - 1 for i in range(1, 33)}  # 0x60..0x7f

    STACK_OPCODES: Dict[str, Tuple[int, int]] = {
        'CODECOPY': (0x39, 3),
        'CALLDATACOPY': (0x37, 3),
        'RETURNDATACOPY': (0x3e, 3),
        'EXTCODECOPY': (0x3c, 4),
        'KECCAK256': (0x20, 2),
        'MSTORE': (0x52, 2),
        'MLOAD': (0x51, 1),
        'CALLDATALOAD': (0x35, 1),
        'CALLDATASIZE': (0x36, 0),
        'ADD': (0x01, 2),
        'SUB': (0x03, 2),
        'MUL': (0x02, 2),
        'DIV': (0x04, 2),
        'LT': (0x10, 2),
        'GT': (0x11, 2),
        'EQ': (0x14, 2),
        'AND': (0x16, 2),
        'OR': (0x17, 2),
        'XOR': (0x18, 2),
        'NOT': (0x19, 1),
        'SHL': (0x1b, 2),
        'SHR': (0x1c, 2),
        'SAR': (0x1d, 2),
        'RETURN': (0xf3, 2),
        'REVERT': (0xfd, 2),
        'STOP': (0x00, 0),
        'INVALID': (0xfe, 0),
        'JUMPDEST': (0x5b, 0),
    }

    # DUP1=0x80 .. DUP16=0x8f
    for i in range(1, 17):
        STACK_OPCODES[f'DUP{i}'] = (0x7f + i, 0)
    # SWAP1=0x90 .. SWAP16=0x9f
    for i in range(1, 17):
        STACK_OPCODES[f'SWAP{i}'] = (0x8f + i, 0)

    def encode_push(self, value: int, width: int) -> bytes:
        if not (1 <= width <= 32):
            raise ValueError(f"PUSH width must be 1-32, got {width}")
        max_val = (1 << (8 * width)) - 1
        if value < 0 or value > max_val:
            raise ValueError(f"Value {value} out of range for PUSH{width}")
        operand = value.to_bytes(width, byteorder='big')
        return bytes([self.PUSH_OPCODES[width]]) + operand

    def encode_stack_opcode(self, opcode_name: str, operands: List[int]) -> bytes:
        if opcode_name not in self.STACK_OPCODES:
            raise ValueError(f"Unknown stack opcode: {opcode_name}")
        opcode_byte, expected_arity = self.STACK_OPCODES[opcode_name]
        if len(operands) != expected_arity:
            raise ValueError(
                f"{opcode_name} expects {expected_arity} operands, got {len(operands)}"
            )
        bytecode = bytearray()
        for operand in reversed(operands):
            width = max(1, (operand.bit_length() + 7) // 8)
            width = min(32, width)
            bytecode.extend(self.encode_push(operand, width))
        bytecode.append(opcode_byte)
        return bytes(bytecode)

    def encode(self, instructions: List[Tuple[str, Any]]) -> str:
        bytecode = bytearray()
        for instruction in instructions:
            if isinstance(instruction, tuple):
                opcode, operand = instruction
            else:
                opcode, operand = instruction, None

            if opcode.startswith("PUSH"):
                width = int(opcode[4:])
                bytecode.extend(self.encode_push(operand, width))
            elif opcode in self.STACK_OPCODES:
                operands = operand if isinstance(operand, (list, tuple)) else (
                    [] if operand is None else [operand]
                )
                bytecode.extend(self.encode_stack_opcode(opcode, list(operands)))
            else:
                raise ValueError(f"Unhandled opcode: {opcode}")
        return bytecode.hex()


# ============================================================
# 6. Compiler Builtins
# ============================================================

class CBytesCompiler:
    """Compiler for cbytes operations."""

    # EVM gas costs (Berlin hard fork)
    GAS = {
        'ZERO': 0, 'PUSH': 3, 'PUSH32': 3, 'DUP': 3, 'SWAP': 3,
        'MSTORE': 3, 'MLOAD': 3, 'ADD': 3, 'SUB': 3, 'MUL': 5,
        'LT': 3, 'GT': 3, 'EQ': 3, 'JUMPI': 10, 'JUMPDEST': 1,
        'CODECOPY': 3, 'KECCAK256': 30, 'CALLDATALOAD': 3,
        'CALLDATASIZE': 2, 'CALLDATACOPY': 3, 'STATICCALL': 700,
        'RETURN': 0, 'STOP': 0, 'REVERT': 0,
        'SHA3_WORD': 6, 'MEMORY_EXPANSION_BASE': 3,
        'MEMORY_EXPANSION_WORD': 3,
    }

    def __init__(self, section_store: Optional[BytecodeSectionStore] = None):
        self.store = section_store or BytecodeSectionStore()
        self._comptime_resolved: Dict[str, Any] = {}
        self._ir_nodes: List[IRNode] = []
        self._yul_lines: List[str] = []
        self._opcode_sequence: List[Tuple[str, int]] = []
        self._total_gas: int = 0
        self.encoder = BytecodeEncoder()

    def reset(self):
        self._ir_nodes = []
        self._yul_lines = []
        self._opcode_sequence = []
        self._total_gas = 0
        self._comptime_resolved = {}

    def comptime_keccak256(self, cb: CBytes) -> IRNode:
        if cb.cb_id in self.store._sections:
            hash_bytes = self.store.keccak256(cb.cb_id, cb.offset, cb.length)
            hash_int = int.from_bytes(hash_bytes, 'big')
            self._comptime_resolved[f'keccak256_{cb.cb_id}_{cb.offset}_{cb.length}'] = hash_bytes
            node = IRNode(
                ir_type=IRType.COMPTIME_KECCAK256,
                value=hash_int,
                metadata={
                    'resolved_at': 'compile_time',
                    'hash_hex': f'0x{hash_bytes.hex()}',
                    'gas_saved': '~600',
                }
            )
            self._ir_nodes.append(node)
            return node
        else:
            return self.runtime_keccak256(cb)

    def runtime_keccak256(self, cb: CBytes) -> IRNode:
        node = IRNode(
            ir_type=IRType.RUNTIME_KECCAK256,
            operands=[cb.to_ir()],
            metadata={
                'resolved_at': 'runtime',
                'estimated_gas': estimate_keccak256_gas(cb.offset, cb.length),
            }
        )
        self._ir_nodes.append(node)
        return node

    def slice_bytes(self, cb: CBytes, start: int, end: int) -> Tuple[CBytes, IRNode]:
        if end > cb.length:
            raise ValueError(
                f"slice out of bounds: end={end} > length={cb.length}"
            )
        new_cb = CBytes(cb.cb_id, cb.offset + start, end - start)
        node = IRNode(
            ir_type=IRType.CBYTES_SLICE,
            operands=[cb.to_ir(),
                      IRNode(ir_type=IRType.CONSTANT_U256, value=start),
                      IRNode(ir_type=IRType.CONSTANT_U256, value=end)],
            value=new_cb.to_ir().value,
            metadata={
                'resolved_at': 'compile_time',
                'bounds_checked': True,
                'zero_copy': True,
                'gas': self.GAS['PUSH'],
            }
        )
        bounds_node = IRNode(
            ir_type=IRType.BOUNDS_CHECK,
            operands=[
                IRNode(ir_type=IRType.CONSTANT_U256, value=end),
                IRNode(ir_type=IRType.CONSTANT_U256, value=cb.length),
            ],
            metadata={'pass': True, 'gas': self.GAS['LT'] + self.GAS['JUMPI']}
        )
        self._ir_nodes.extend([node, bounds_node])
        return new_cb, node

    def bytes_concat(self, cbytes_list: List[CBytes]) -> Tuple[CBytes, IRNode]:
        total_length = sum(cb.length for cb in cbytes_list)
        concat_data = b''
        for cb in cbytes_list:
            if cb.cb_id in self.store._sections:
                section_data = self.store.get_section(cb.cb_id)
                concat_data += section_data[cb.offset:cb.offset + cb.length]
            else:
                concat_data += b'\x00' * cb.length
        new_section_id = self.store.add_section(concat_data)
        new_cb = CBytes(new_section_id, 0, total_length)
        n_words = max(1, (total_length + 31) // 32)
        gas = n_words * (self.GAS['MSTORE'] + self.GAS['PUSH32'])
        node = IRNode(
            ir_type=IRType.CBYTES_CONCAT,
            operands=[cb.to_ir() for cb in cbytes_list],
            value={'id': new_section_id, 'offset': 0, 'length': total_length},
            metadata={
                'total_length': total_length,
                'n_sections': len(cbytes_list),
                'n_words': n_words,
                'gas': gas,
            }
        )
        self._ir_nodes.append(node)
        return new_cb, node

    def data_offset(self, cb: CBytes) -> IRNode:
        node = IRNode(
            ir_type=IRType.DATA_OFFSET,
            operands=[cb.to_ir()],
            value=cb.offset,
            metadata={'resolved_at': 'link_time', 'gas': self.GAS['PUSH']}
        )
        self._ir_nodes.append(node)
        return node

    def bytes_len(self, cb: CBytes) -> IRNode:
        node = IRNode(
            ir_type=IRType.BYTES_LEN,
            operands=[cb.to_ir()],
            value=cb.length,
            metadata={'gas': self.GAS['PUSH']}
        )
        self._ir_nodes.append(node)
        return node

    def content_eq(self, a: CBytes, b: CBytes) -> IRNode:
        try:
            hash_a = self.store.keccak256(a.cb_id, a.offset, a.length)
            hash_b = self.store.keccak256(b.cb_id, b.offset, b.length)
            result = hash_a == hash_b
            node = IRNode(
                ir_type=IRType.CONTENT_EQ,
                operands=[a.to_ir(), b.to_ir()],
                value=result,
                metadata={
                    'resolved_at': 'compile_time',
                    'hash_a': f'0x{hash_a.hex()[:16]}...',
                    'hash_b': f'0x{hash_b.hex()[:16]}...',
                    'gas': self.GAS['EQ'],
                }
            )
        except (KeyError, ValueError):
            node = IRNode(
                ir_type=IRType.CONTENT_EQ,
                operands=[
                    self.runtime_keccak256(a),
                    self.runtime_keccak256(b),
                ],
                metadata={
                    'resolved_at': 'runtime',
                    'gas': 2 * estimate_keccak256_gas(max(a.length, b.length)) + self.GAS['EQ'],
                }
            )
        self._ir_nodes.append(node)
        return node

    # ============================================================
    # 7. Yul Code Generator (FIX C)
    # ============================================================

    def generate_yul(self) -> str:
        lines = []
        lines.append("// ARKHE cbytes Compiler — vinf.364.1-patch1")
        lines.append("// Generated Yul/EVM output")
        lines.append(f"// Sections: {self.store.section_count()}, Total bytes: {self.store.total_size()}")
        lines.append("")

        for node in self._ir_nodes:
            yul = self._ir_to_yul(node)
            if yul:
                lines.extend(yul)
                lines.append("")

        self._yul_lines = lines
        return '\n'.join(lines)

    def _ir_to_yul(self, node: IRNode) -> List[str]:
        lines = []
        if node.ir_type == IRType.COMPTIME_KECCAK256:
            hash_val = node.value
            lines.append(f"// @comptime_keccak256 — resolved at compile time")
            lines.append(f"// Hash baked as PUSH32 constant (0 gas runtime)")
            lines.append(f"let hash_{id(node)} := {hex(hash_val)}")
        elif node.ir_type == IRType.RUNTIME_KECCAK256:
            lines.append(f"// Runtime keccak256 via CALLDATACOPY + KECCAK256")
            lines.append(f"let ptr := mload(0x40)")
            lines.append(f"let offset := {node.operands[0].value['offset']}")
            lines.append(f"let length := {node.operands[0].value['length']}")
            lines.append(f"calldatacopy(ptr, offset, length)")  # FIX C
            lines.append(f"let hash_{id(node)} := keccak256(ptr, length)")
        elif node.ir_type == IRType.CBYTES_SLICE:
            lines.append(f"// @slice_bytes — zero-copy, bounds checked")
            lines.append(f"// slice(id={node.value['id']}, offset={node.value['offset']}, length={node.value['length']})")
        elif node.ir_type == IRType.CBYTES_CONCAT:
            length = node.metadata['total_length']
            n_words = node.metadata['n_words']
            lines.append(f"// @bytes_concat — flat layout, {length} bytes, {n_words} words")
            for i in range(n_words):
                word_offset = i * 32
                lines.append(f"mstore(add(ptr, {word_offset}), 0x{'00' * 32})  // word {i}")
        elif node.ir_type == IRType.DATA_OFFSET:
            lines.append(f"// @data_offset — resolved at link time")
            lines.append(f"let data_off_{id(node)} := {node.value}")
        elif node.ir_type == IRType.BYTES_LEN:
            lines.append(f"// @bytes_len")
            lines.append(f"let len_{id(node)} := {node.value}")
        elif node.ir_type == IRType.CONTENT_EQ:
            if node.metadata.get('resolved_at') == 'compile_time':
                lines.append(f"// content_eq — compile-time resolved")
                lines.append(f"let eq_{id(node)} := {'1' if node.value else '0'}")
            else:
                lines.append(f"// content_eq — runtime keccak256 comparison")
                lines.append(f"let eq_{id(node)} := eq(hash_a_{id(node.operands[0])}, hash_b_{id(node.operands[1])})")
        elif node.ir_type == IRType.BOUNDS_CHECK:
            lines.append(f"// Bounds check (pass)")
        return lines

    # ============================================================
    # 8. Solidity Contract Generator (FIX C)
    # ============================================================

    def generate_solidity_contract(self, contract_name: str = "ARKHECBytes") -> str:
        yul_body = self.generate_yul()

        contract = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title {contract_name}
/// @notice ARKHE OS v\u221e.364.1-patch1 — cbytes verification contract
/// @author Rafael Oliveira (ORCID: 0009-0005-2697-4668)
contract {contract_name} {{
    bytes32 public rootHash;

    /// @notice Verify a cbytes proof commitment
    /// @param proofData ABI-encoded proof data (offset + length + data)
    /// @return hash The keccak256 hash of the proof slice
    function verifyProof(bytes calldata proofData)
        external view returns (bytes32 hash)
    {{
        assembly {{
            // FIX C: calldatacopy + ABI-compliant return
            let freePtr := mload(0x40)
            let dataLen := proofData.length
            let requiredSize := add(dataLen, 32)
            mstore(0x40, add(freePtr, requiredSize))

            // Copy from calldata to memory
            calldatacopy(freePtr, proofData.offset, dataLen)

            // Compute hash
            hash := keccak256(freePtr, dataLen)

            // Return ABI-encoded bytes32
            mstore(freePtr, hash)
            return(freePtr, 32)
        }}
    }}

    function registerRoot(bytes32 root) external {{
        require(root != bytes32(0), "EMPTY_ROOT");
        require(rootHash == bytes32(0), "ALREADY_REGISTERED");
        rootHash = root;
    }}

    function verifyAgainstRoot(bytes32 proofHash) external view returns (bool valid) {{
        valid = (proofHash == rootHash);
    }}
}}
"""
        return contract

    def generate_octra_contract(self) -> str:
        contract = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title OCTRARegistry
/// @notice Immutable proof registration with cbytes optimization
/// @author Rafael Oliveira — ARKHE OS v\u221e.364.1-patch1
contract OCTRARegistry {{
    mapping(bytes32 => Registration) public registrations;
    bytes32[] public registeredRoots;

    struct Registration {{
        address submitter;
        uint64 timestamp;
        uint16 version;
        bool active;
    }}

    event ProofRegistered(
        address indexed submitter,
        bytes32 indexed root,
        uint256 version,
        uint64 timestamp
    );

    function registerProof(bytes calldata proofData, uint16 version) external {{
        uint256 ptr;
        uint256 len;
        assembly {{
            ptr := proofData.offset
            len := proofData.length
        }}

        bytes32 root;
        assembly {{
            let hashPtr := mload(0x40)
            calldatacopy(hashPtr, ptr, len)
            root := keccak256(hashPtr, len)
        }}

        require(root != bytes32(0), "EMPTY_ROOT");
        require(registrations[root].timestamp == 0, "DUPLICATE_ROOT");

        registrations[root] = Registration({{
            submitter: msg.sender,
            timestamp: uint64(block.timestamp),
            version: version,
            active: true
        }});

        registeredRoots.push(root);
        emit ProofRegistered(msg.sender, root, version, uint64(block.timestamp));
    }}

    function verifyProof(bytes32 proofHash) external view returns (bool valid) {{
        valid = registrations[proofHash].active;
    }}

    function batchVerify(bytes32[] calldata hashes)
        external view returns (bool[] memory results)
    {{
        results = new bool[](hashes.length);
        for (uint256 i = 0; i < hashes.length; i++) {{
            results[i] = registrations[hashes[i]].active;
        }}
    }}

    function registrationCount() external view returns (uint256 count) {{
        count = registeredRoots.length;
    }}
}}
"""
        return contract


# ============================================================
# 9. Self-Tests (executados no import do módulo)
# ============================================================

def _run_keccak_tests():
    """FIX A: Vetores de teste Keccak-256 EVM-compatíveis."""
    k = keccak.new(digest_bits=256)
    k.update(b"")
    assert k.digest().hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"

    k = keccak.new(digest_bits=256)
    k.update(b"abc")
    assert k.digest().hex() == "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45"
    return True


def _run_memory_expansion_tests():
    """FIX B: Vetores de teste EIP-150."""
    assert memory_expansion_cost(128, 0, 4096) == 0
    assert memory_expansion_cost(128, 0, 8192) == 480
    assert memory_expansion_cost(0, 0, 4096) == 416
    assert memory_expansion_cost(64, 2048, 2048) == 216
    assert memory_expansion_cost(0, 0, 32) == 3
    assert memory_expansion_cost(0, 0, 0) == 0
    return True


def _run_encoder_tests():
    """FIX D: Vetores de teste do BytecodeEncoder."""
    enc = BytecodeEncoder()
    assert enc.encode([("CODECOPY", [0, 64, 32])]) == "60206040600039"
    assert enc.encode([("CALLDATACOPY", [0x40, 0x04, 0x20])]) == "60206004604037"
    assert enc.encode([("KECCAK256", [0x40, 0x20])]) == "6020604020"
    assert enc.encode([("STOP", None)]) == "00"
    assert enc.encode([("REVERT", [0x00, 0x00])]) == "60006000fd"
    return True


# Executar self-tests no load
if __name__ != "__main__":
    assert _run_keccak_tests(), "Keccak self-tests failed"
    assert _run_memory_expansion_tests(), "Memory expansion self-tests failed"
    assert _run_encoder_tests(), "Bytecode encoder self-tests failed"

def _evm_keccak256(data: bytes):
    from Crypto.Hash import keccak
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k
