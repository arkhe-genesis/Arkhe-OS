// backend/src/api/consent.js
import express from 'express';
import { z } from 'zod';
import { CathedralAuth, ZKProofVerifier } from 'cathedral-sdk/node';
import { ConsentModel } from '../models/Consent.js';

const router = express.Router();

// Instância de autenticação Cathedral (valida Ω-Tokens JWT)
const auth = new CathedralAuth({
  issuer: process.env.CATHEDRAL_ISSUER,
  jwksUri: process.env.CATHEDRAL_JWKS_URI,
});

// ===== SCHEMAS DE VALIDAÇÃO (Zod) =====

const grantConsentSchema = z.object({
  citizenDid: z.string().startsWith('did:cathedral:'),
  category: z.enum(['health', 'location', 'financial', 'behavioral']),
  purpose: z.enum(['research', 'service', 'personalization', 'compliance']),
  duration: z.object({
    type: z.enum(['temporal', 'event', 'indefinite']).optional(),
    endTimestamp: z.number().optional(),
    eventTrigger: z.string().optional(),
  }).optional(),
  revocable: z.boolean().default(true),
});

/**
 * POST /consent/grant
 */
router.post('/grant',
  auth.requireValidOmegaToken({ scopes: ['consent:grant'] }),
  async (req, res) => {
    try {
      const validated = grantConsentSchema.parse(req.body);

      if (validated.citizenDid !== req.omegaToken.sub) {
        return res.status(403).json({ error: 'Token não corresponde ao cidadão' });
      }

      const receipt = await ConsentModel.grant({
        ...validated,
        grantedBy: req.omegaToken.sub,
        grantedAt: new Date(),
        ipAddress: req.ip,
        userAgent: req.get('User-Agent'),
        requestId: req.id,
      });

      res.status(201).json({
        success: true,
        receipt,
      });

    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: 'Validação falhou', details: error.errors });
      }
      console.error('Consent grant error:', error);
      res.status(500).json({ error: 'Erro interno ao processar consentimento' });
    }
  }
);

/**
 * GET /consent/status/:citizenDid
 */
router.get('/status/:citizenDid',
  auth.requireValidOmegaToken(),
  async (req, res) => {
    try {
      const { citizenDid } = req.params;

      if (req.omegaToken.sub !== citizenDid && !req.omegaToken.scopes?.includes('audit:consent')) {
        return res.status(403).json({ error: 'Acesso não autorizado' });
      }

      const status = await ConsentModel.getStatus(citizenDid);
      res.json(status);

    } catch (error) {
      console.error('Consent status error:', error);
      res.status(500).json({ error: 'Erro ao consultar estado de consentimento' });
    }
  }
);

export default router;
