# Arkhe OS Build Instructions

This document explains how to build the Arkhe OS executable locally.

1. Ensure Python 3.12 and Node.js 20+ are installed.
2. Install Python dependencies: `pip install -r requirements.txt`
3. Install UI dependencies: `cd ui/desktop && npm install`
4. Build the UI: `npm run build`
5. Bundle via PyInstaller (or equivalent packaging tool) the backend alongside the built frontend.

The `arkhe-os` directory contains the foundational layer using the OS canonical substrates directly through Python.
