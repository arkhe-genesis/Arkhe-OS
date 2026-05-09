-- Arkhe-Chain Governance Initial Schema
CREATE DATABASE arkhe_governance;
\c arkhe_governance;

CREATE TABLE IF NOT EXISTS blocks (
    id SERIAL PRIMARY KEY,
    index INTEGER UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    previous_hash TEXT NOT NULL,
    nonce INTEGER NOT NULL,
    coherence_score DOUBLE PRECISION NOT NULL,
    hash TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    memory_fragment TEXT,
    phase_signature TEXT,
    block_id INTEGER REFERENCES blocks(id)
);
