import https from 'https';
import { logger } from './server/logger.js';

https.get('https://etherscan.io/verifySig/303737', {
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
  }
}, (res) => {
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  res.on('end', () => {
    const addressMatch = data.match(/0x[a-fA-F0-9]{40}/g);
    const msgMatch = data.match(/<textarea[^>]*>([\s\S]*?)<\/textarea>/g);
    
    logger.info("Addresses found: " + (addressMatch ? [...new Set(addressMatch)].join(', ') : "None"));
    logger.info("Textareas found: " + (msgMatch ? msgMatch.join(', ') : "None"));
  });
}).on('error', (err) => {
  logger.error('Error: ' + err.message);
});
