"""
client.py — HTTP client for llama-server (llama.cpp)

Usage:
    from client import LlamaClient, GenerationConfig

    client = LlamaClient("http://localhost:8080")

    # Simple completion
    text = client.complete("Explain quantum entanglement in one paragraph.")
    print(text)

    # Chat completion (OpenAI-compatible)
    reply = client.chat([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"},
    ])
    print(reply)

    # Streaming
    for chunk in client.stream("Tell me a story about a robot."):
        print(chunk, end="", flush=True)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Generator, Iterator, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ── Configuration ────────────────────────────────────────────────────────────

@dataclass
class GenerationConfig:
    """Parameters forwarded to llama-server /completion."""
    max_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop: list[str] = field(default_factory=list)
    seed: int = -1                  # -1 = random
    stream: bool = False
    cache_prompt: bool = True       # reuse KV-cache across calls with same prefix


@dataclass
class CompletionResult:
    """Parsed response from llama-server."""
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    stop_type: str                  # "stop" | "length" | "abort"
    generation_ms: float
    seal: str                       # SHA3-256 of the generated text

    @property
    def tokens_per_second(self) -> float:
        if self.generation_ms <= 0:
            return 0.0
        return self.completion_tokens / (self.generation_ms / 1000)

    def __repr__(self) -> str:
        return (
            f"CompletionResult("
            f"tokens={self.completion_tokens}, "
            f"speed={self.tokens_per_second:.1f} tok/s, "
            f"stop={self.stop_type!r}"
            f")"
        )


# ── Client ───────────────────────────────────────────────────────────────────

class LlamaClient:
    """
    Thin HTTP client for llama-server.

    llama-server exposes three relevant endpoints:
      GET  /health        → {"status": "ok"}
      POST /completion    → raw completion
      POST /v1/chat/completions → OpenAI-compatible chat
      GET  /metrics       → Prometheus text
      GET  /props         → model metadata
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: int = 120,
        retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = self._build_session(retries)

    # ── Session setup ────────────────────────────────────────────────────────

    def _build_session(self, retries: int) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"Content-Type": "application/json"})
        return session

    # ── Health / metadata ────────────────────────────────────────────────────

    def health(self) -> dict:
        """Returns {"status": "ok"} when server is ready."""
        resp = self._session.get(f"{self.base_url}/health", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def is_ready(self) -> bool:
        """Non-raising health check."""
        try:
            return self.health().get("status") == "ok"
        except Exception:
            return False

    def wait_until_ready(self, max_wait: float = 60.0, poll: float = 2.0) -> bool:
        """
        Poll /health until server is ready or timeout expires.
        Returns True if ready, False on timeout.
        """
        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            if self.is_ready():
                return True
            time.sleep(poll)
        return False

    def props(self) -> dict:
        """Model metadata: context length, model name, etc."""
        resp = self._session.get(f"{self.base_url}/props", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def metrics(self) -> str:
        """Raw Prometheus metrics text."""
        resp = self._session.get(f"{self.base_url}/metrics", timeout=10)
        resp.raise_for_status()
        return resp.text

    # ── Core completion ──────────────────────────────────────────────────────

    def complete(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> CompletionResult:
        """
        Send a raw completion request.

        Example:
            result = client.complete("The capital of France is")
            print(result.text)  # " Paris."
        """
        cfg = config or GenerationConfig()
        payload = self._build_payload(prompt, cfg)

        t0 = time.monotonic()
        resp = self._session.post(
            f"{self.base_url}/completion",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        elapsed_ms = (time.monotonic() - t0) * 1000

        data = resp.json()
        text = data.get("content", "")

        return CompletionResult(
            text=text,
            prompt_tokens=data.get("tokens_evaluated", 0),
            completion_tokens=data.get("tokens_predicted", 0),
            total_tokens=data.get("tokens_evaluated", 0) + data.get("tokens_predicted", 0),
            stop_type=data.get("stop_type", "unknown"),
            generation_ms=elapsed_ms,
            seal=hashlib.sha3_256(text.encode()).hexdigest(),
        )

    def stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> Iterator[str]:
        """
        Stream completion tokens as they are generated.

        Example:
            for token in client.stream("Write a haiku about the sea:"):
                print(token, end="", flush=True)
        """
        cfg = config or GenerationConfig(stream=True)
        cfg.stream = True
        payload = self._build_payload(prompt, cfg)

        with self._session.post(
            f"{self.base_url}/completion",
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                # Server-sent events format: "data: {...}"
                if isinstance(line, bytes):
                    line = line.decode()
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        token = data.get("content", "")
                        if token:
                            yield token
                        if data.get("stop", False):
                            break
                    except json.JSONDecodeError:
                        continue

    # ── Chat completion (OpenAI-compatible) ──────────────────────────────────

    def chat(
        self,
        messages: list[dict],
        config: Optional[GenerationConfig] = None,
        model: str = "local-model",
    ) -> str:
        """
        OpenAI-compatible chat completion.

        messages format:
            [
                {"role": "system", "content": "You are helpful."},
                {"role": "user",   "content": "Hello!"},
            ]

        Returns the assistant's reply text.
        """
        cfg = config or GenerationConfig()
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stop": cfg.stop or None,
            "stream": False,
        }

        resp = self._session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Unexpected response structure: {data}") from exc

    def chat_stream(
        self,
        messages: list[dict],
        config: Optional[GenerationConfig] = None,
        model: str = "local-model",
    ) -> Iterator[str]:
        """Streaming variant of chat()."""
        cfg = config or GenerationConfig(stream=True)
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "stream": True,
        }

        with self._session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode()
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _build_payload(self, prompt: str, cfg: GenerationConfig) -> dict:
        payload: dict = {
            "prompt": prompt,
            "n_predict": cfg.max_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "top_k": cfg.top_k,
            "repeat_penalty": cfg.repeat_penalty,
            "cache_prompt": cfg.cache_prompt,
            "stream": cfg.stream,
        }
        if cfg.stop:
            payload["stop"] = cfg.stop
        if cfg.seed != -1:
            payload["seed"] = cfg.seed
        return payload


# ── Batch helper ─────────────────────────────────────────────────────────────

class BatchClient:
    """
    Run multiple prompts concurrently using a thread pool.

    Example:
        batch = BatchClient(client, max_workers=4)
        prompts = ["Question 1?", "Question 2?", "Question 3?"]
        results = batch.run(prompts)
    """

    def __init__(self, client: LlamaClient, max_workers: int = 4):
        self.client = client
        self.max_workers = max_workers

    def run(
        self,
        prompts: list[str],
        config: Optional[GenerationConfig] = None,
    ) -> list[CompletionResult | Exception]:
        from concurrent.futures import ThreadPoolExecutor, as_completed

        futures = {}
        results: list[CompletionResult | Exception] = [None] * len(prompts)  # type: ignore

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for idx, prompt in enumerate(prompts):
                future = executor.submit(self.client.complete, prompt, config)
                futures[future] = idx

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as exc:
                    results[idx] = exc

        return results


# ── CLI quick test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    client = LlamaClient(url)

    print(f"Connecting to {url}...")
    if not client.wait_until_ready(max_wait=10):
        print("ERROR: server not ready after 10s")
        sys.exit(1)

    props = client.props()
    print(f"Model: {props.get('default_generation_settings', {}).get('model', 'unknown')}")
    print(f"Context: {props.get('default_generation_settings', {}).get('n_ctx', '?')} tokens")
    print()

    prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "The sky is blue because"

    print(f"Prompt: {prompt!r}")
    print("Response (streaming):", flush=True)
    for token in client.stream(prompt, GenerationConfig(max_tokens=128)):
        print(token, end="", flush=True)
    print()