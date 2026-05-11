import { logger } from './server/logger.js';

const strings = ['Tfv7p3lpIENjUGiD', 'Tfvtp31ENjUGiD', '7fv7p31ENjUGiD'];

const b64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function reverseBits(n) {
  let res = 0;
  for (let i = 0; i < 6; i++) {
    res = (res << 1) | (n & 1);
    n >>= 1;
  }
  return res;
}

strings.forEach(s => {
  let out = '';
  for (let i = 0; i < s.length; i++) {
    const idx = b64.indexOf(s[i]);
    if (idx !== -1) {
      out += b64[reverseBits(idx)];
    } else {
      out += s[i];
    }
  }
  const padded = out.padEnd(Math.ceil(out.length / 4) * 4, '=');
  const buf = Buffer.from(padded, 'base64');
  logger.info(`${s} -> ${out} -> ${buf.toString('utf8')} hex: ${buf.toString('hex')}`);
});
