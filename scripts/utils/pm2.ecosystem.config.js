module.exports = {
  apps: [
    {
      name: 'api-nest',
      cwd: './arkhe-chain-node/apps/api-nest',
      script: 'npm',
      args: 'run start:prod',
      instances: 'max',
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
    },
    {
      name: 'telemetry-fastify',
      cwd: './arkhe-chain-node/apps/telemetry-fastify',
      script: 'npm',
      args: 'run start',
      instances: 2,
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production',
        PORT: 3002,
      },
    },
    {
      name: 'express-bridge',
      cwd: './arkhe-chain-node/apps/express-bridge',
      script: 'npm',
      args: 'run start',
      instances: 1,
      env: {
        NODE_ENV: 'production',
        PORT: 3001,
      },
    },
  ],
};
