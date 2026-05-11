const https = require('https');

https.get('https://api.etherscan.io/api?module=account&action=txlist&address=0xbf7da1f568684889a69a5bed9f1311f703985590&startblock=0&endblock=99999999&page=1&offset=10&sort=asc', {
  headers: {
    'User-Agent': 'Mozilla/5.0'
  }
}, (res) => {
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  res.on('end', async () => {
    const { logger } = await import('./server/logger.ts');
    logger.info(data);
  });
}).on('error', async (err) => {
  const { logger } = await import('./server/logger.ts');
  logger.error("Error: " + err.message);
});
