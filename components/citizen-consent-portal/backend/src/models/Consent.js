// backend/src/models/Consent.js
import mongoose from 'mongoose';
import { CathedralCodex } from 'cathedral-sdk/node';

const consentSchema = new mongoose.Schema({
  citizenDid: { type: String, required: true, index: true },
  category: { type: String, required: true },
  purpose: { type: String, required: true },
  granted: { type: Boolean, default: true },
  grantedAt: { type: Date, default: Date.now },
  revokedAt: { type: Date, default: null },
  duration: {
    type: { type: String, enum: ['temporal', 'event', 'indefinite'], default: 'indefinite' },
    endTimestamp: Number,
    eventTrigger: String,
  },
  receiptId: { type: String, required: true, unique: true },
  codexAnchor: { artifactId: String, contentHash: String, anchoredAt: Date },
}, { timestamps: true });

consentSchema.index({ citizenDid: 1, category: 1, purpose: 1 }, { unique: true });

consentSchema.methods.anchorToCodex = async function() {
  const codex = new CathedralCodex({ endpoint: process.env.CATHEDRAL_CODEX_API });

  const artifact = {
    citizenDid: this.citizenDid,
    category: this.category,
    purpose: this.purpose,
    grantedAt: this.grantedAt,
  };

  const anchor = await codex.storeArtifact({
    artifactId: `consent_${this.receiptId}`,
    content: artifact,
  });

  this.codexAnchor = {
    artifactId: anchor.artifactId,
    contentHash: anchor.contentHash,
    anchoredAt: new Date(),
  };

  return this.save();
};

consentSchema.statics.grant = async function(data) {
  const receiptId = `receipt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const consent = new this({ ...data, receiptId });
  await consent.save();
  await consent.anchorToCodex();
  return consent;
};

consentSchema.statics.getStatus = async function(citizenDid) {
  const consents = await this.find({ citizenDid }).lean();
  const categories = {};

  for (const c of consents) {
    if (!categories[c.category]) categories[c.category] = {};
    categories[c.category][c.purpose] = {
      granted: c.granted && !c.revokedAt,
      receiptId: c.receiptId,
    };
  }

  return { citizenDid, categories };
};

export const ConsentModel = mongoose.model('Consent', consentSchema);
