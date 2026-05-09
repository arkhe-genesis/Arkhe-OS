import asyncio
import time
import hashlib
import weakref
from typing import Any, Callable, Dict, Optional, List
from collections import OrderedDict

class ArkheCacheVault:
    """
    Arkhe(n) Cache Vault implementing 10 advanced caching strategies.
    Integrated with Phase Coherence (lambda2) for dynamic TTL and behavior.
    """
    def __init__(self, oscillator: Any, max_l1_size: int = 100, default_ttl: int = 300):
        self.oscillator = oscillator
        self.l1_cache = OrderedDict()  # 4. LRU Eviction
        self.max_l1_size = max_l1_size
        self.default_ttl = default_ttl
        self.metadata = {} # {key: {"expires": timestamp, "hits": int}}
        self._locks = weakref.WeakValueDictionary() # 5. Cache Stampede protection (Fixed Memory Leak)
        self.write_behind_queue = asyncio.Queue()
        self.hot_key_threshold = 10
        self._write_behind_task = None

    def _ensure_background_tasks(self):
        if self._write_behind_task is None:
            try:
                self._write_behind_task = asyncio.create_task(self._process_write_behind())
            except RuntimeError:
                # Event loop not running yet, will be started on first use
                pass

    def _get_coherence(self) -> float:
        return getattr(self.oscillator, 'lambda2', 1.0)

    def _get_dynamic_ttl(self, base_ttl: int) -> int:
        # Higher coherence -> longer TTL
        coherence = self._get_coherence()
        return int(base_ttl * (0.5 + coherence))

    def _get_lock(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    # 0. Cache Aside (Lazy Loading)
    async def get_aside(self, key: str, fetch_func: Callable) -> Any:
        value = self.get(key)
        if value is not None:
            return value

        # 5. Cache Stampede protection (Meltdown)
        lock = self._get_lock(key)

        async with lock:
            # Double check after acquiring lock
            value = self.get(key)
            if value is not None:
                return value

            print(f"[ARKHE_CACHE] Aside Fetch: {key}")
            value = await fetch_func()
            self.set(key, value)
            return value

    # 1. Write Through
    async def set_write_through(self, key: str, value: Any, db_writer: Callable):
        print(f"[ARKHE_CACHE] Write Through: {key}")
        # Write to DB first (or simultaneously)
        await db_writer(key, value)
        # Then update cache
        self.set(key, value)

    # 2. Write Behind (Async)
    async def set_write_behind(self, key: str, value: Any, db_writer: Callable):
        self._ensure_background_tasks()
        print(f"[ARKHE_CACHE] Write Behind (Queued): {key}")
        self.set(key, value)
        await self.write_behind_queue.put((key, value, db_writer))

    async def _process_write_behind(self):
        while True:
            key, value, db_writer = await self.write_behind_queue.get()
            try:
                await db_writer(key, value)
                print(f"[ARKHE_CACHE] Write Behind Persisted: {key}")
            except Exception as e:
                print(f"[ARKHE_CACHE] Write Behind Error: {e}")
            finally:
                self.write_behind_queue.task_done()

    # 3. Cache Invalidation
    def invalidate(self, key: str):
        if key in self.l1_cache:
            del self.l1_cache[key]
        if key in self.metadata:
            del self.metadata[key]
        # 6. Distributed Consistency (Broadcast Invalidation)
        self._broadcast_invalidation(key)

    def _broadcast_invalidation(self, key: str):
        # Mocking distributed sync
        print(f"[ARKHE_CACHE] DISTRIBUTED_SYNC: Invalidating {key} across mesh.")

    # 4. TTL & Explicit Eviction (LRU)
    def get(self, key: str) -> Optional[Any]:
        if key not in self.l1_cache:
            return None

        meta = self.metadata.get(key, {})
        if time.time() > meta.get("expires", 0):
            print(f"[ARKHE_CACHE] TTL Expired: {key}")
            self.invalidate(key)
            return None

        # 4. Move to end (LRU)
        self.l1_cache.move_to_end(key)
        meta["hits"] = meta.get("hits", 0) + 1

        # 7. Hot Key Handling: Promote if hit count is high
        if meta["hits"] > self.hot_key_threshold:
            self._handle_hot_key(key)

        return self.l1_cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        # 4. LRU Efficiency Fix
        if key in self.l1_cache:
            self.l1_cache.move_to_end(key)
        elif len(self.l1_cache) >= self.max_l1_size:
            evicted_key, _ = self.l1_cache.popitem(last=False)
            print(f"[ARKHE_CACHE] Evicting (LRU): {evicted_key}")
            if evicted_key in self.metadata:
                del self.metadata[evicted_key]

        effective_ttl = self._get_dynamic_ttl(ttl or self.default_ttl)
        self.l1_cache[key] = value
        self.metadata[key] = {
            "expires": time.time() + effective_ttl,
            "hits": 0,
            "hot": False
        }

    # 7. Hot Keys (Skew handling)
    def _handle_hot_key(self, key: str):
        if not self.metadata[key].get("hot"):
            self.metadata[key]["hot"] = True
            print(f"[ARKHE_CACHE] Hot Key Detected: {key}. Increasing replication/priority.")

    # 8. Cache Warming (Preload)
    async def warm_up(self, prefetch_map: Dict[str, Callable]):
        print("[ARKHE_CACHE] Initiating Cache Warming...")
        for key, fetch_func in prefetch_map.items():
            value = await fetch_func()
            self.set(key, value)
        print("[ARKHE_CACHE] Cache Warmup Complete.")

    # 9. Multi-layer Caching (L1/L2)
    async def get_multi_layer(self, key: str, l2_fetcher: Callable, origin_fetcher: Callable) -> Any:
        # Check L1 (In-Memory)
        val = self.get(key)
        if val: return val

        # Check L2 (Distributed/Persistent)
        print(f"[ARKHE_CACHE] L1 Miss, checking L2: {key}")
        val = await l2_fetcher(key)
        if val:
            self.set(key, val)
            return val

        # Check Origin
        print(f"[ARKHE_CACHE] L2 Miss, fetching from Origin: {key}")
        val = await origin_fetcher()
        self.set(key, val)
        return val
