// ═══════════════════════════════════════════════════════════════════
// ARKHE SUBSTRATE REGISTRATION — Registro on-chain dos substratos
// ═══════════════════════════════════════════════════════════════════

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class SubstrateRegistrar {
  constructor(substratesPath = path.join(__dirname, '..', 'substrates')) {
    this.substratesPath = substratesPath;
    this.registry = [];
  }

  async registerAll() {
    const sDir = path.join(this.substratesPath, 's');
    if (!fs.existsSync(sDir)) {
      console.log('[REGISTRY] Nenhum substrato encontrado em', sDir);
      return;
    }

    const dirs = fs.readdirSync(sDir).filter(d => /^\d+_/.test(d));
    for (const dir of dirs) {
      const tomlPath = path.join(sDir, dir, 'substrate.toml');
      if (fs.existsSync(tomlPath)) {
        const toml = fs.readFileSync(tomlPath, 'utf8');
        const id = parseInt(dir.split('_')[0]);
        const name = dir.slice(dir.indexOf('_') + 1);
        const seal = crypto.createHash('sha3-256').update(toml).digest('hex');
        const service = {
          service_id: `arkhe-substrate-${id}`,
          name,
          seal,
          phi_c: this._extractPhiC(toml),
          cross_links: this._extractCrossLinks(toml),
          registered_at: new Date().toISOString(),
          registrant: 'ORCID 0009-0005-2697-4668',
        };
        this.registry.push(service);
        console.log(`[REGISTRY] Registrado: ${service.service_id} (Φ_C=${service.phi_c})`);
      }
    }

    // Publicar via Telegraph
    if (global.telegraph) {
      global.telegraph.publish('/external/telegraph', {
        metric: 'substrate_registration',
        value: this.registry.length,
        unit: 'substrates',
      });
    }
  }

  _extractPhiC(toml) {
    const match = toml.match(/standard_phi_c\s*=\s*([\d.]+)/);
    return match ? parseFloat(match[1]) : 0.0;
  }

  _extractCrossLinks(toml) {
    const links = [];
    const regex = /\{\s*id\s*=\s*(\d+).*?type\s*=\s*"(\w+)".*?bidirectional\s*=\s*(true|false)/g;
    let match;
    while ((match = regex.exec(toml)) !== null) {
      links.push({ id: parseInt(match[1]), type: match[2], bidirectional: match[3] === 'true' });
    }
    return links;
  }
}

module.exports = SubstrateRegistrar;