
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { gql } from 'apollo-server-express';

import { state } from './state';

// GraphQL Schema Definition (SDL)
export const typeDefs = gql`
  type Metric {
    musd: Float
    musda: Float
    wmaBc: Float
  }

  type Shard {
    id: String
    status: String
  }

  type Topology {
    nodes: Int
    yangBaxterValid: Boolean
  }

  type SystemState {
    threatLevel: String
    activeThreat: String
    currentLambda: Float
    metrics: Metric
    shards: [Shard]
    topology: Topology
  }

  type Query {
    getSystemState: SystemState
    getCoherence: Float
    getShard(id: String!): Shard
  }

  type Mutation {
    resetSystem: Boolean
    triggerThreat(type: String!): Boolean
  }
`;

// GraphQL Resolvers
export const resolvers = {
  Query: {
    getSystemState: () => state,
    getCoherence: () => state.currentLambda,
    getShard: (_: any, { id }: { id: string }) => state.shards.find((s: any) => s.id === id),
  },
  Mutation: {
    resetSystem: () => {
      state.threatLevel = 'normal';
      state.activeThreat = null;
      state.currentLambda = 0.98;
      return true;
    },
    triggerThreat: (_: any, { type }: { type: string }) => {
      state.threatLevel = 'critical';
      state.activeThreat = type;
      state.currentLambda = 0.45;
      return true;
    },
  },
};
