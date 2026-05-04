// backend/src/server.js
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import morgan from 'morgan';
import { CathedralSDK } from 'cathedral-sdk/node';
import consentRoutes from './api/consent.js';
import { errorHandler } from './middleware/errorHandler.js';
import { connectDatabase } from './db/connect.js';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:5173'],
  credentials: true,
}));

app.use(morgan('combined'));
app.use(express.json());

// Health check com Ω-score
app.get('/health', async (req, res) => {
  try {
    const sdk = new CathedralSDK({ endpoint: process.env.CATHEDRAL_API });
    const omega = await sdk.getGlobalOmega();

    res.json({
      status: 'ok',
      omega: {
        global: omega.global_omega,
        threshold: { healthy: 0.85, critical: 0.70 },
      },
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    res.status(500).json({ status: 'error', error: err.message });
  }
});

app.use('/api/v1/consent', consentRoutes);
app.use(errorHandler);

const start = async () => {
  try {
    await connectDatabase(process.env.MONGODB_URI);

    app.listen(PORT, () => {
      console.log(`🚀 Servidor rodando em http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('❌ Falha ao iniciar:', error);
    process.exit(1);
  }
};

start();
