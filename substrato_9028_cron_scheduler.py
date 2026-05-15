#!/usr/bin/env python3
"""
Entry point for Substrato 9028 — Arkhe Cron Scheduler.
"""

import asyncio
import logging
from arkhe_scheduler.cron_scheduler import CathedralCronScheduler

logging.basicConfig(level=logging.INFO)

async def main():
    scheduler = CathedralCronScheduler()
    await scheduler.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested")
