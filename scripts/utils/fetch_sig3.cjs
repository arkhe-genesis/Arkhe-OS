const https = require('https');

https.get('https://etherscan.io/verifySig/303724', {
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
  }
}, (res) => {
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  res.on('end', async () => {
    const { logger } = await import('./server/logger.ts');
    const match = data.match(/0x[a-fA-F0-9]{40}/g);
    if (match) {
      logger.info("Addresses found: " + [...new Set(match)].join(', '));
    }
  });
}).on('error', async (err) => {
  const { logger } = await import('./server/logger.ts');
  logger.error("Error: " + err.message);
});
