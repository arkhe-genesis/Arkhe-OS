// server/api/gateway.ts
// API HTTP para o Polymath-Polyglot Parser

import express from 'express';
// @ts-ignore
import { PolyglotParserWasm } from '../../pkg/arkhe_polyglot_parser.js';

const app = express();
app.use(express.json({ limit: '10mb' }));

const parser = new PolyglotParserWasm();

// Detectar linguagem
app.post('/api/v1/detect', (req, res) => {
    const { source, filename } = req.body;
    const result = parser.detect_language(source, filename);
    res.json(result);
});

// Parse
app.post('/api/v1/parse', (req, res) => {
    const { source, filename } = req.body;
    try {
        const result = parser.parse(source, filename);
        res.json(result);
    } catch(e) {
        res.status(400).json({ error: e });
    }
});

// Transpilar
app.post('/api/v1/transpile', (req, res) => {
    const { source, from, to } = req.body;
    try {
        const result = parser.transpile(source, from, to);
        res.json(result);
    } catch(e) {
        res.status(400).json({ error: e });
    }
});

// Análise semântica
app.post('/api/v1/analyze', (req, res) => {
    const { source, language } = req.body;
    const result = parser.analyze(source, language);
    res.json(result);
});

// Diff temporal
app.post('/api/v1/diff', (req, res) => {
    // const { oldVersion, newVersion } = req.body;
    // const delta = parser.temporalDiff(oldVersion, newVersion);
    res.json({});
});

// Listar linguagens
app.get('/api/v1/languages', (req, res) => {
    res.json(parser.list_languages());
});

// Upload de plugin
app.post('/api/v1/plugins/upload', (req, res) => {
    const { name, data } = req.body;
    parser.register_language(name, Buffer.from(data, 'base64'));
    res.json({ status: 'ok' });
});

app.listen(8080, () => {
    console.log('ARKHE P³ API Gateway running on port 8080');
});
