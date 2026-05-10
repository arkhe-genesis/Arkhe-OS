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
    const idx = data.indexOf('0xbf7da1f568684889a69a5bed9f1311f703985590');
    if (idx !== -1) {
      logger.info("Context 1: " + data.substring(idx - 100, idx + 100));
    }
    const idx2 = data.indexOf('0x71c7656ec7ab88b098defb751b7401b5f6d8976f');
    if (idx2 !== -1) {
      logger.info("Context 2: " + data.substring(idx2 - 100, idx2 + 100));
    }
  });
}).on('error', async (err) => {
  const { logger } = await import('./server/logger.ts');
  logger.error("Error: " + err.message);
});
