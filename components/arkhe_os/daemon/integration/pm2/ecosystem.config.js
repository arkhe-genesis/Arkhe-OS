// integration/pm2/ecosystem.config.js
module.exports = {
  apps: [
    {
      name: 'arkhe-agi',
      script: './dist/daemon/index.js',
      interpreter: 'node',
      interpreter_args: '--max-old-space-size=4096', // 4GB heap limit

      // Environment
      env: {
        NODE_ENV: 'production',
        ARKHE_NODE_ID: process.env.ARKHE_NODE_ID || 'default-node',
        ARKHE_CONFIG_PATH: process.env.ARKHE_CONFIG_PATH || './config/production.yaml',
        ARKHE_LOG_LEVEL: process.env.ARKHE_LOG_LEVEL || 'info',
      },

      // Process management
      instances: 1, // Single instance for stateful AGI; use cluster mode only if stateless
      exec_mode: 'fork', // Not cluster, to preserve LFIR state in memory
      autorestart: true,
      watch: false,
      max_memory_restart: '3G', // Restart if memory exceeds 3GB

      // Logging
      output: './logs/arkhe-agi-out.log',
      error: './logs/arkhe-agi-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // Health & monitoring
      min_uptime: '30s', // Consider restart successful after 30s uptime
      max_restarts: 10, // Max restarts before giving up
      restart_delay: 2000, // 2s between restart attempts

      // Graceful shutdown
      kill_timeout: 30000, // 30s for graceful shutdown
      listen_timeout: 10000, // 10s for port binding

      // Environment-specific overrides
      env_production: {
        ARKHE_LOG_LEVEL: 'info',
        ARKHE_HEALTH_ENDPOINT: 'http://localhost:3000/health',
        ARKHE_METRICS_PORT: 9090,
      },

      // Integration with Arkhe health checks
      health_check: {
        endpoint: '/health',
        port: 3000,
        timeout: 5000,
        interval: 30000,
        // Custom check: verify Φ_C > threshold
        custom: async (http) => {
          const response = await http.get('http://localhost:3000/health/detailed');
          const data = JSON.parse(response.data);
          const coherence = data.metrics?.coherence_score ?? 0;
          return coherence >= 0.85; // Minimum coherence for "healthy"
        },
      },
    },
  ],
};
