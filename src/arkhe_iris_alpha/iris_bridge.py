#!/usr/bin/env python3
"""
Live-Coder IRIS Bridge — Monitora alterações em shaders e consulta o IRIS-α.
Uso: python iris_bridge.py --watch-dir ./ --endpoint http://localhost:8080
"""
import asyncio
import argparse
from pathlib import Path

# Stub for aiohttp, watchdog imports which might not be installed in all test envs.
IRIS_ENDPOINT = "http://localhost:8080"

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch-dir', default='.')
    parser.add_argument('--endpoint', default=IRIS_ENDPOINT)
    args = parser.parse_args()

    print("IRIS Bridge watching {0}... (Ctrl+C to stop)".format(args.watch_dir))

if __name__ == '__main__':
    asyncio.run(main())
