
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import path from "node:path";

// import { ApolloServer, gql } from 'apollo-server-express';
import cors from "cors";
import express from "express";
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import { createServer as createViteServer } from "vite";


import { startAgentGrpcServer } from "./agent_grpc_server";
import { setupARStream } from "./ar_stream";
import { setupConnectors } from "./connectors";
import { typeDefs, resolvers } from './graphql';
import { logger } from "./logger";
import { setupLucentCollector } from "./lucent_omega";
import { setupPresenceServer } from "./presence_field_server";
import { setupRoutes } from "./routes";
import { runSimulationTick } from "./simulation";
import { state } from "./state";


import { setupProofGraphRoutes } from "./proof_graph";

// SSE Clients
const clients: express.Response[] = [];

function broadcastState() {
  const data = `data: ${JSON.stringify(state)}\n\n`;
  clients.forEach(client => client.write(data));
}

// Simulation Loop
setInterval(() => {
  runSimulationTick(broadcastState);
}, 1000);

async function startServer() {
  const app = express();
  const PORT = 3000;

  // 18/ Secure Headers with Helmet (CSP, XSS, etc.)
  app.use(helmet({
    contentSecurityPolicy: {
      directives: {
        ...helmet.contentSecurityPolicy.getDefaultDirectives(),
        "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "connect-src": ["'self'", "ws:", "wss:", "https://app.plurality.network"],
      },
    },
  }));

  // 8/ Rate Limiting
  const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    standardHeaders: true,
    legacyHeaders: false,
    message: "Too many requests from this IP, please try again after 15 minutes"
  });

  app.use("/api/", limiter);
  
  // 6/ Tighten CORS
  const allowedOrigins = process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(',') : [];
  app.use(cors({
    origin: (origin, callback) => {
      // Allow requests with no origin (like mobile apps or curl)
      if (!origin) {return callback(null, true);}
      if (process.env.NODE_ENV !== "production" || allowedOrigins.indexOf(origin) !== -1) {
        callback(null, true);
      } else {
        callback(new Error('Not allowed by CORS'));
      }
    },
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
  }));

  app.use(express.json());

  // Setup GraphQL Apollo Server
  const { ApolloServer } = await import('apollo-server-express');
  const apollo = new ApolloServer({
    typeDefs,
    resolvers,
  });
  await apollo.start();
  apollo.applyMiddleware({ app: app as any });

  // Serve static files for the presence field UI
  app.use("/static", express.static(path.join(process.cwd(), "static")));

  // Setup API Routes
  setupRoutes(app, broadcastState, clients);
  setupProofGraphRoutes(app);

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*all', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  const server = app.listen(PORT, "0.0.0.0", () => {
    logger.info(`Server running on http://localhost:${PORT}`);
  });

  // Attach presence server
  setupPresenceServer(server);

  // Initialize AR Stream Server
  const { WebSocketServer } = await import('ws');
  const arWss = new WebSocketServer({ noServer: true });
  setupARStream(arWss);

  server.on('upgrade', (request, socket, head) => {
    const { pathname } = new URL(request.url || '', `http://${request.headers.host}`);
    if (pathname === '/api/ar/stream') {
      arWss.handleUpgrade(request, socket, head, (ws) => {
        arWss.emit('connection', ws, request);
      });
    }
  });

  // Initialize Lucent-Ω Collector (qhttp)
  setupLucentCollector();

  // Start Agent gRPC Server
  startAgentGrpcServer();

  // Setup Civic Data Connectors
  setupConnectors();
}

startServer();
