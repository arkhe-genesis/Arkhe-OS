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
    const match = data.match(/Signer Address.*?0x[a-fA-F0-9]{40}/i);
    if (match) {
      logger.info("Signer: " + match[0]);
    } else {
      const allMatches = data.match(/0x[a-fA-F0-9]{40}/g);
      logger.info("All: " + [...new Set(allMatches)].join(', '));
    }
  });
}).on('error', async (err) => {
  const { logger } = await import('./server/logger.ts');
  logger.error("Error: " + err.message);
});
