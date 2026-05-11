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
    logger.info("Response length: " + data.length);
    // Look for the message text
    const match = data.match(/<textarea[^>]*>([\s\S]*?)<\/textarea>/g);
    if (match) {
      logger.info("Textareas found:");
      match.forEach(m => logger.info(m));
    } else {
      logger.info("No textareas found. Dumping some HTML:");
      logger.info(data.substring(0, 2000));
    }
  });
}).on('error', async (err) => {
  const { logger } = await import('./server/logger.ts');
  logger.error("Error: " + err.message);
});
