# src/arkhe_os/parser/platform_abstraction.py
"""
Platform abstraction layer for cross-platform compatibility.
Handles OS-specific paths, threading, memory mapping, and acceleration backends.
"""
import sys
import os
import platform
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class PlatformInfo:
    """Detected platform information."""

    def __init__(self):
        self.system = platform.system()  # 'Linux', 'Darwin', 'Windows'
        self.machine = platform.machine()  # 'x86_64', 'arm64', 'AMD64'
        self.python_version = sys.version_info
        self.is_64bit = sys.maxsize > 2**32

        # Platform-specific flags
        self.is_linux = self.system == 'Linux'
        self.is_macos = self.system == 'Darwin'
        self.is_windows = self.system == 'Windows'
        self.is_apple_silicon = self.is_macos and self.machine == 'arm64'
        self.is_wsl = self.is_linux and 'microsoft' in platform.release().lower()

        # Acceleration backend detection
        self.acceleration_backend = self._detect_acceleration()

    def _detect_acceleration(self) -> str:
        """Detect available acceleration backend."""
        try:
            import torch
            if torch.cuda.is_available():
                return 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return 'mps'  # Apple Silicon Metal
            else:
                return 'cpu'
        except ImportError:
            return 'cpu'

    @property
    def default_num_threads(self) -> int:
        """Recommended number of threads for parallel operations."""
        # Avoid oversubscription on macOS with Accelerate framework
        if self.is_macos:
            return min(os.cpu_count() or 4, 8)
        return os.cpu_count() or 4

    @property
    def path_separator(self) -> str:
        """OS-appropriate path separator."""
        return '\\' if self.is_windows else '/'

    @property
    def home_dir(self) -> Path:
        """Cross-platform home directory."""
        if self.is_windows:
            return Path(os.environ.get('USERPROFILE', Path.home()))
        return Path.home()

# Global platform instance
PLATFORM = PlatformInfo()

def get_cache_dir(subdir: Optional[str] = None) -> Path:
    """Get platform-appropriate cache directory."""
    if PLATFORM.is_windows:
        base = Path(os.environ.get('LOCALAPPDATA', PLATFORM.home_dir / 'AppData' / 'Local'))
    elif PLATFORM.is_macos:
        base = PLATFORM.home_dir / 'Library' / 'Caches'
    else:  # Linux
        base = Path(os.environ.get('XDG_CACHE_HOME', PLATFORM.home_dir / '.cache'))

    cache_dir = base / 'arkhe' / 'rsp-parser'
    if subdir:
        cache_dir /= subdir
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_config_dir() -> Path:
    """Get platform-appropriate config directory."""
    if PLATFORM.is_windows:
        base = Path(os.environ.get('APPDATA', PLATFORM.home_dir / 'AppData' / 'Roaming'))
    elif PLATFORM.is_macos:
        base = PLATFORM.home_dir / 'Library' / 'Application Support'
    else:  # Linux
        base = Path(os.environ.get('XDG_CONFIG_HOME', PLATFORM.home_dir / '.config'))

    config_dir = base / 'arkhe' / 'rsp-parser'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def memory_mapped_array(filename: str, shape: tuple, dtype) -> Any:
    """Create memory-mapped array with platform-optimized flags."""
    import numpy as np

    if PLATFORM.is_windows:
        # Windows: use mode='w+' for compatibility
        return np.memmap(filename, dtype=dtype, mode='w+', shape=shape)
    else:
        # Unix-like: can use 'r+' for better performance
        return np.memmap(filename, dtype=dtype, mode='r+', shape=shape)

def parallel_map(func: Callable, items: list, max_workers: Optional[int] = None) -> list:
    """Cross-platform parallel map with appropriate backend."""
    from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

    # macOS: prefer threads over processes due to fork() issues with certain libs
    use_threads = PLATFORM.is_macos or PLATFORM.is_windows

    n_workers = max_workers or PLATFORM.default_num_threads

    if use_threads:
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            return list(executor.map(func, items))
    else:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            return list(executor.map(func, items))

def set_thread_affinity(thread_id: int, cpu_ids: list):
    """Set thread CPU affinity (Linux only, no-op on other platforms)."""
    if not PLATFORM.is_linux:
        return  # Not supported on macOS/Windows via Python stdlib

    try:
        import psutil
        proc = psutil.Process()
        proc.cpu_affinity(cpu_ids)
    except (ImportError, AttributeError, PermissionError):
        logger.debug(f"Could not set CPU affinity for thread {thread_id}")
