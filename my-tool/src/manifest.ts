import { defineManifest } from "@opensea/tool-sdk"

export const manifest = defineManifest({
  type: "https://ercs.ethereum.org/ERCS/erc-8257#tool-manifest-v1",
  name: "arkhe-gateway-tool",
  description: "ARKHE Gateway Publish and Verify",
  endpoint: "https://my-tool.vercel.app",
  inputs: {
    type: "object",
    properties: {
      operation: {
        type: "string",
        enum: ["publish", "verify", "health", "registry"],
        description: "The operation to perform on the ARKHE Gateway."
      },
      substrate: {
        type: "string",
        enum: ["870-B", "865", "864", "863", "862", "861", "860", "859"],
        description: "The originating substrate identifier (required for publish)"
      },
      action: {
        type: "string",
        enum: ["ANCHOR", "DECREE", "DEPLOY", "SIMULATE", "SCAN", "PROPOSE"],
        description: "Action type to publish (required for publish)"
      },
      sequence: {
        type: "string",
        description: "Glosa 245 canonical binary sequence (36 bits)"
      },
      metadata: {
        type: "object",
        description: "Additional metadata payload"
      },
      payload: {
        type: "object",
        description: "Technical payload for the substrate"
      },
      hash: {
        type: "string",
        description: "SHA3-256 seal to verify (required for verify)"
      }
    },
    required: ["operation"],
  },
  outputs: {
    type: "object",
    properties: {
      result: { type: "string" },
      data: { type: "object" }
    },
  },
  creatorAddress: "0x0000000000000000000000000000000000000000",
})
