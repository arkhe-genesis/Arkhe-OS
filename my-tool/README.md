# my-tool

An ERC-8257 compliant AI agent tool deployed on Vercel.

## Setup

```bash
npm install
```

## Development

```bash
npx vercel dev
```

## Deploy

```bash
npx vercel
```

## Register onchain

```bash
npx @opensea/tool-sdk verify https://my-tool.vercel.app/.well-known/ai-tool/my-tool.json
npx @opensea/tool-sdk register --metadata https://my-tool.vercel.app/.well-known/ai-tool/my-tool.json --network base
```
