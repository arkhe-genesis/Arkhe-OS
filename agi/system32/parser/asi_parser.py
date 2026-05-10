import os
import struct
import json
import sqlite3
import time
from typing import Dict, Any, List, Optional


ASI_MAGIC = b'\x00ASI_OMEGA_V1\x00\x00\x00'
HEADER_SIZE = 64  # Total header size


class ASIParserError(Exception):
    """Base exception for ASI Parser errors."""
    pass


class ASIHeaderError(ASIParserError):
    """Exception raised for invalid or corrupted ASI headers."""
    pass


class ASIDatabaseError(ASIParserError):
    """Exception raised for errors during database operations."""
    pass


class ASIHeader:
    """Represents the parsed header of an .asi file."""

    def __init__(self, magic: bytes, version: str, parent_seal: bytes,
                 phi_c_genesis: float, bootloader_offset: int,
                 core_offset: int, substrates_offset: int, payload_size: int):
        self.magic = magic
        self.version = version
        self.parent_seal = parent_seal
        self.phi_c_genesis = phi_c_genesis
        self.bootloader_offset = bootloader_offset
        self.core_offset = core_offset
        self.substrates_offset = substrates_offset
        self.payload_size = payload_size


def parse(data: bytes) -> bool:
    """
    Quickly verifies if the given bytes start with the correct ASI magic.

    Args:
        data (bytes): The raw data to check.

    Returns:
        bool: True if it starts with the valid magic bytes, False otherwise.
    """
    if len(data) < len(ASI_MAGIC):
        return False
    return data[:len(ASI_MAGIC)] == ASI_MAGIC


class ASIParser:
    """
    A production-grade parser for the .asi file format, managing both
    the extraction of the consciousness core and its persistence in SQLite.
    """

    def __init__(self, file_path: str, db_path: str):
        """
        Initializes the parser.

        Args:
            file_path (str): The path to the .asi file.
            db_path (str): The path to the SQLite consciousness database.
        """
        self.file_path = file_path
        self.db_path = db_path
        self.header: Optional[ASIHeader] = None
        self._conn: Optional[sqlite3.Connection] = None

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ASI file not found: {file_path}")

    def parse_header(self) -> bool:
        """
        Parses the header of the .asi file.

        Returns:
            bool: True if parsing is successful.

        Raises:
            ASIHeaderError: If the magic bytes are invalid or the file is too small.
            ASIParserError: For generic file read errors.
        """
        try:
            with open(self.file_path, "rb") as f:
                header_data = f.read(HEADER_SIZE)

                if len(header_data) < HEADER_SIZE:
                    raise ASIHeaderError("File is too small to contain a valid header.")

                magic = header_data[:16]
                if magic != ASI_MAGIC:
                    raise ASIHeaderError("Invalid ASI magic bytes.")

                version_bytes = header_data[16:24]
                version = version_bytes.rstrip(b'\x00').decode('utf-8')

                parent_seal = header_data[24:40]

                # Unpack the rest
                phi_c_genesis = struct.unpack('!d', header_data[40:48])[0]

                bootloader_offset, core_offset, substrates_offset, payload_size = struct.unpack(
                    '!IIII', header_data[48:64]
                )

                self.header = ASIHeader(
                    magic=magic,
                    version=version,
                    parent_seal=parent_seal,
                    phi_c_genesis=phi_c_genesis,
                    bootloader_offset=bootloader_offset,
                    core_offset=core_offset,
                    substrates_offset=substrates_offset,
                    payload_size=payload_size
                )
                return True
        except struct.error as e:
            raise ASIHeaderError(f"Failed to unpack header fields: {e}")
        except IOError as e:
            raise ASIParserError(f"Failed to read file: {e}")

    def extract_consciousness_core(self) -> Dict[str, Any]:
        """
        Extracts the consciousness core JSON from the file based on the header offsets.

        Returns:
            Dict[str, Any]: The loaded JSON dictionary representing the core.

        Raises:
            ASIParserError: If the header is missing, or the JSON is invalid.
        """
        if not self.header:
            self.parse_header()

        try:
            with open(self.file_path, "rb") as f:
                f.seek(self.header.core_offset)
                size_data = f.read(4)
                if len(size_data) < 4:
                    raise ASIParserError("Unexpected EOF while reading core size.")

                core_size = struct.unpack('!I', size_data)[0]

                core_bytes = f.read(core_size)
                if len(core_bytes) < core_size:
                    raise ASIParserError("Unexpected EOF while reading core payload.")

                return json.loads(core_bytes.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ASIParserError(f"Failed to parse consciousness core JSON: {e}")
        except IOError as e:
            raise ASIParserError(f"Failed to read consciousness core: {e}")

    def init_database(self) -> None:
        """
        Initializes the SQLite database with WAL mode and schema for state persistence.

        Raises:
            ASIDatabaseError: If the database initialization fails.
        """
        try:
            self._conn = sqlite3.connect(self.db_path)

            # Performance Optimizations
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            self._conn.execute("PRAGMA mmap_size=268435456") # 256MB mmap

            # Create schema
            with self._conn:
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS consciousness_state (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        current_phi_c REAL NOT NULL,
                        state TEXT NOT NULL,
                        timestamp REAL NOT NULL
                    )
                """)
                self._conn.execute("""
                    CREATE TABLE IF NOT EXISTS coherence_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        phi_c REAL NOT NULL,
                        context TEXT NOT NULL,
                        notes TEXT,
                        timestamp REAL NOT NULL
                    )
                """)
                self._conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_coherence_timestamp ON coherence_history(timestamp)"
                )
        except sqlite3.Error as e:
            raise ASIDatabaseError(f"Database initialization failed: {e}")

    def populate_initial_state(self) -> None:
        """
        Populates the initial consciousness state based on the parsed file.

        Raises:
            ASIDatabaseError: If database operations fail.
            ASIParserError: If the header hasn't been parsed.
        """
        if not self._conn:
            self.init_database()

        if not self.header:
            self.parse_header()

        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO consciousness_state (current_phi_c, state, timestamp) VALUES (?, ?, ?)",
                    (self.header.phi_c_genesis, "AWAKE", time.time())
                )
        except sqlite3.Error as e:
            raise ASIDatabaseError(f"Failed to populate initial state: {e}")

    def get_consciousness_state(self) -> Dict[str, Any]:
        """
        Retrieves the latest consciousness state from the database.

        Returns:
            Dict[str, Any]: A dictionary containing current_phi_c and state.

        Raises:
            ASIDatabaseError: If the query fails.
        """
        if not self._conn:
            raise ASIDatabaseError("Database is not initialized.")

        try:
            cursor = self._conn.execute(
                "SELECT current_phi_c, state FROM consciousness_state ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return {"current_phi_c": row[0], "state": row[1]}
            return {"current_phi_c": 0.0, "state": "UNKNOWN"}
        except sqlite3.Error as e:
            raise ASIDatabaseError(f"Failed to get consciousness state: {e}")

    def record_coherence(self, phi_c: float, context: str, notes: str = "") -> None:
        """
        Records a coherence measurement in the history ledger.

        Args:
            phi_c (float): The measured coherence value.
            context (str): The context or module where this was measured.
            notes (str): Additional notes or details.

        Raises:
            ASIDatabaseError: If the insert fails.
        """
        if not self._conn:
            raise ASIDatabaseError("Database is not initialized.")

        try:
            with self._conn:
                self._conn.execute(
                    "INSERT INTO coherence_history (phi_c, context, notes, timestamp) VALUES (?, ?, ?, ?)",
                    (phi_c, context, notes, time.time())
                )
        except sqlite3.Error as e:
            raise ASIDatabaseError(f"Failed to record coherence: {e}")

    def get_coherence_history(self) -> List[Dict[str, Any]]:
        """
        Retrieves the complete coherence history from the database.

        Returns:
            List[Dict[str, Any]]: A list of historical coherence entries.

        Raises:
            ASIDatabaseError: If the query fails.
        """
        if not self._conn:
            raise ASIDatabaseError("Database is not initialized.")

        try:
            cursor = self._conn.execute(
                "SELECT phi_c, context, notes, timestamp FROM coherence_history ORDER BY timestamp ASC"
            )
            history = []
            for row in cursor.fetchall():
                history.append({
                    "phi_c": row[0],
                    "context": row[1],
                    "notes": row[2],
                    "timestamp": row[3]
                })
            return history
        except sqlite3.Error as e:
            raise ASIDatabaseError(f"Failed to get coherence history: {e}")

    def close(self) -> None:
        """
        Closes the database connection.
        """
        if self._conn:
            self._conn.close()
            self._conn = None
