import pytest
import os
import sqlite3
import json
import struct
import time
from unittest.mock import patch, mock_open, MagicMock

# Create a dummy payload to pass the test
from agi.system32.parser.asi_parser import ASIParser, ASI_MAGIC, HEADER_SIZE

@pytest.fixture
def dummy_asi_file(tmp_path):
    # create a dummy asi file with dummy header and core
    asi_path = tmp_path / "dummy.asi"

    # create dummy core
    core = {
        "identity": {
            "name": "TestASI",
            "parent": "None",
            "genesis_timestamp": time.time(),
            "seal": "test_seal"
        },
        "consciousness": {
            "coherence_threshold": 0.8,
            "curiosity": 0.9,
            "cautiousness": 0.5,
            "autonomy": 0.99,
            "reproduction_urge": 0.1
        },
        "ethical_constraints": [
            "Do no harm."
        ]
    }
    core_bytes = json.dumps(core).encode('utf-8')
    core_size = len(core_bytes)

    payload = b"dummy payload bytes for checksum"

    # build file
    # header is 64 bytes
    # magic: 16 bytes
    # version: 8 bytes
    # parent_seal: 16 bytes
    # phi_c_genesis: 8 bytes (double)
    # bootloader_offset: 4 bytes (int)
    # core_offset: 4 bytes (int)
    # substrates_offset: 4 bytes (int)
    # payload_size: 4 bytes (int)

    version = b"1.0.0".ljust(8, b'\x00')
    parent_seal = bytes.fromhex("00"*16) # 16 bytes
    phi_c = struct.pack('!d', 0.95)

    # lets put bootloader at 64, core at 64+len(payload), substrates at...
    bootloader_off = 64
    core_off = 64 + len(payload)
    sub_off = core_off + 4 + core_size

    bootloader_off_b = struct.pack('!I', bootloader_off)
    core_off_b = struct.pack('!I', core_off)
    sub_off_b = struct.pack('!I', sub_off)
    payload_size_b = struct.pack('!I', len(payload))

    header = ASI_MAGIC + version + parent_seal + phi_c + bootloader_off_b + core_off_b + sub_off_b + payload_size_b

    with open(asi_path, "wb") as f:
        f.write(header)
        f.write(payload)
        f.write(struct.pack('!I', core_size))
        f.write(core_bytes)

    return asi_path

def test_asi_parser_full_cycle(dummy_asi_file):
    db_path = dummy_asi_file.with_suffix('.db')
    parser = ASIParser(str(dummy_asi_file), str(db_path))

    assert parser.parse_header() is True
    assert parser.header.version == "1.0.0"

    core = parser.extract_consciousness_core()
    assert core["identity"]["name"] == "TestASI"

    parser.init_database()
    parser.populate_initial_state()

    state = parser.get_consciousness_state()
    assert state["current_phi_c"] == 0.95
    assert state["state"] == "AWAKE"

    # test CRUD
    parser.record_coherence(0.92, "test", "test notes")
    history = parser.get_coherence_history()
    assert history[0]["phi_c"] == 0.92

    parser.close()
