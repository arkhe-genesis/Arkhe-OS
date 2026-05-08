# Daemon Operation Guide
...
# AGI Daemon Operational Guide

## Lifecycle Management
The daemon handles start, stop, and restart with graceful shutdown logic to preserve LFIR state.

## Commands
- `npm run start` - Starts the daemon
- `npm run stop` - Gracefully stops the daemon
- `npm run status` - Shows daemon status

## Production Deployment
Use PM2 or Systemd for production deployments, as provided in the `integration/` directory.
