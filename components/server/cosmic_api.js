// server/cosmic_api.js
import express from 'express';
import { ethers } from 'ethers';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import cors from 'cors';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(cors());
app.use(express.json());

// --- Configuração do Contrato ---
const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || '0x9f8E3a2B7c4D1e5F6a8C0b3D2e1F4a5B6c7D8e9';
const CONTRACT_ABI = [
  "function submitSurveyProof(uint[2] a, uint[2][2] b, uint[2] c, uint[2] input, bytes32 surveyId, uint256 redshift, uint256 pOccCommitment, uint256 phiQCommitment) external",
  "function proofs(bytes32) view returns (bytes32 surveyId, uint256 redshift, uint256 pOccCommitment, uint256 phiQCommitment, uint256 timestamp, bool verified)",
  "function rounds(uint256) view returns (uint256 roundId, uint256 z_start, uint256 z_end, uint256 delta_p_max_allowed, uint256 requiredMethodologies, uint256 methodCount, bool consensusReached, bytes32 finalCommitment)",
  "function currentPMinThreshold() view returns (uint256)"
];

const ALCHEMY_KEY = process.env.ALCHEMY_KEY;
const provider = new ethers.providers.JsonRpcProvider(
  `https://eth-sepolia.g.alchemy.com/v2/${ALCHEMY_KEY || 'MOCK'}`
);

const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, provider);

const RELAYER_PRIVATE_KEY = process.env.RELAYER_PRIVATE_KEY;
const relayerWallet = RELAYER_PRIVATE_KEY ? new ethers.Wallet(RELAYER_PRIVATE_KEY, provider) : null;

// --- Middleware de Autenticação ---
const API_KEYS = new Set((process.env.API_KEYS || 'test-key').split(',').filter(Boolean));
function auth(req, res, next) {
  const apiKey = req.headers['x-api-key'];
  if (!apiKey || !API_KEYS.has(apiKey)) {
    return res.status(401).json({ error: 'Unauthorized. Provide a valid API key.' });
  }
  next();
}

// --- Rotas ---

app.get('/api/v1/circuit', auth, (req, res) => {
  res.json({
    wasm_url: `${req.protocol}://${req.get('host')}/circuit/CosmicPoccVerifier.wasm`,
    zkey_url: `${req.protocol}://${req.get('host')}/circuit/CosmicPoccVerifier_final.zkey`,
    instructions: 'Use snarkjs with these files to generate a proof locally.'
  });
});

app.use('/circuit', express.static(path.join(__dirname, '..', 'circuits')));

app.post('/api/v1/proofs', auth, async (req, res) => {
  try {
    const { proof, publicSignals, surveyId, redshift, pOccCommitment, phiQCommitment } = req.body;
    if (!proof || !publicSignals || !surveyId) {
      return res.status(400).json({ error: 'Missing required fields.' });
    }

    if (!relayerWallet) {
        return res.status(500).json({ error: 'Relayer wallet not configured.' });
    }

    const a = [proof.pi_a[0], proof.pi_a[1]];
    const b = [[proof.pi_b[0][1], proof.pi_b[0][0]], [proof.pi_b[1][1], proof.pi_b[1][0]]];
    const c = [proof.pi_c[0], proof.pi_c[1]];
    const input = [publicSignals[0], publicSignals[1]];

    const tx = await contract.connect(relayerWallet).submitSurveyProof(
      a, b, c, input,
      ethers.utils.formatBytes32String(surveyId),
      redshift,
      pOccCommitment,
      phiQCommitment,
      { gasLimit: 500000 }
    );
    await tx.wait();

    res.json({
      success: true,
      transactionHash: tx.hash,
      surveyId,
      explorerUrl: `https://sepolia.etherscan.io/tx/${tx.hash}`
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to submit proof.', details: error.message });
  }
});

app.get('/api/v1/proofs/:surveyId', auth, async (req, res) => {
  try {
    const surveyId = req.params.surveyId;
    const [sid, redshift, pOccCommitment, phiQCommitment, timestamp, verified] = await contract.proofs(
      ethers.utils.formatBytes32String(surveyId)
    );
    res.json({
      surveyId: sid.startsWith('0x') ? ethers.utils.parseBytes32String(sid) : sid,
      redshift: redshift.toString(),
      pOccCommitment: pOccCommitment.toString(),
      phiQCommitment: phiQCommitment.toString(),
      timestamp: new Date(timestamp.toNumber() * 1000).toISOString(),
      verified
    });
  } catch (error) {
    res.status(404).json({ error: 'Survey proof not found.' });
  }
});

app.get('/api/v1/consensus/:roundId', auth, async (req, res) => {
  try {
    const roundId = req.params.roundId;
    const round = await contract.rounds(roundId);
    res.json({
      roundId: round.roundId.toString(),
      redshift_range: [round.z_start.toString(), round.z_end.toString()],
      delta_p_max: round.delta_p_max_allowed.toString(),
      methodologies: {
          required: round.requiredMethodologies.toString(),
          current: round.methodCount.toString()
      },
      consensusReached: round.consensusReached,
      finalCommitment: round.finalCommitment
    });
  } catch (error) {
      res.status(404).json({ error: 'Consensus round not found.' });
  }
});

app.get('/api/v1/parameters', auth, async (req, res) => {
  try {
    const pMin = await contract.currentPMinThreshold();
    res.json({
      P_min: pMin.toString(),
      note: 'P_min scaled by 1e120; divide to get physical value.'
    });
  } catch (error) {
    res.json({ P_min: "1.0e-122", note: "Offline mode. Default threshold." });
  }
});

const PORT = process.env.PORT || 3000;
if (process.env.NODE_ENV !== 'test') {
    app.listen(PORT, () => {
      console.log(`🌌 Cosmic Validator API running on port ${PORT}`);
    });
}

export default app;
