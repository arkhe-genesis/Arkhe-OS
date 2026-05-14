# src/arkhe/os/arkfs.py
"""
ArkFS — Sistema de Arquivos com Selos Canônicos
Cada escrita gera um selo SHA3‑256. Cada leitura verifica a integridade.
"""
import hashlib, json, os, stat, time
from fuse import FUSE, Operations, LoggingMixIn
from typing import Dict

class ArkFS(LoggingMixIn, Operations):
    def __init__(self, mount_point: str):
        self.mount = mount_point
        self.seals: Dict[str, str] = {}  # path → selo
        self.files: Dict[str, bytes] = {}

    def create(self, path: str, mode: int, fi=None):
        self.files[path] = b""
        self.seals[path] = hashlib.sha3_256(b"").hexdigest()[:16]
        return 0

    def write(self, path: str, data: bytes, offset: int, fh=None):
        current = self.files.get(path, b"")
        new_data = current[:offset] + data + current[offset+len(data):]
        self.files[path] = new_data
        self.seals[path] = hashlib.sha3_256(new_data).hexdigest()[:16]
        return len(data)

    def read(self, path: str, size: int, offset: int, fh=None):
        data = self.files.get(path, b"")
        if data:
            expected_seal = self.seals.get(path, "")
            actual_seal = hashlib.sha3_256(data).hexdigest()[:16]
            if expected_seal and actual_seal != expected_seal:
                raise IOError(f"Integrity violation in {path}")
        return data[offset:offset+size]

    def getattr(self, path: str, fh=None):
        if path not in self.files and path != "/":
            raise FileNotFoundError(path)
        now = time.time()
        return dict(st_mode=(stat.S_IFDIR | 0o755) if path == "/" else (stat.S_IFREG | 0o644),
                    st_nlink=2, st_size=len(self.files.get(path, b"")),
                    st_ctime=now, st_mtime=now, st_atime=now)

if __name__ == "__main__":
    print("ArkFS initialized.")
