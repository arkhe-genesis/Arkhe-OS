import { createToolHandler } from "@opensea/tool-sdk"
import { z } from "zod"
import { manifest } from "./manifest.js"

const InputSchema = z.object({
  operation: z.enum(["publish", "verify", "health", "registry"]),
  substrate: z.enum(["870-B", "865", "864", "863", "862", "861", "860", "859"]).optional(),
  action: z.enum(["ANCHOR", "DECREE", "DEPLOY", "SIMULATE", "SCAN", "PROPOSE"]).optional(),
  sequence: z.string().optional(),
  metadata: z.record(z.string(), z.any()).optional(),
  payload: z.record(z.string(), z.any()).optional(),
  hash: z.string().optional()
})

const OutputSchema = z.object({
  result: z.string(),
  data: z.record(z.string(), z.any()).optional()
})

export const toolHandler = createToolHandler({
  manifest,
  inputSchema: InputSchema,
  outputSchema: OutputSchema,
  handler: async input => {
    const bridgeUrl = "http://127.0.0.1:8700"

    try {
      if (input.operation === "publish") {
        if (!input.substrate) throw new Error("substrate is required for publish")
        if (!input.action) throw new Error("action is required for publish")

        const res = await fetch(`${bridgeUrl}/publish`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            substrate: input.substrate,
            action: input.action,
            sequence: input.sequence,
            metadata: input.metadata || {},
            payload: input.payload || {}
          })
        })
        const data = await res.json()
        if (!res.ok) throw new Error(JSON.stringify(data))
        return { result: "Success", data }
      } else if (input.operation === "verify") {
        if (!input.hash) throw new Error("hash is required for verify")

        let h = input.hash.toLowerCase().trim()
        if (h.startsWith("0x")) h = h.slice(2)

        const res = await fetch(`${bridgeUrl}/verify/${h}`)
        const data = await res.json()
        if (!res.ok) throw new Error(JSON.stringify(data))
        return { result: "Success", data }
      } else if (input.operation === "health") {
        const res = await fetch(`${bridgeUrl}/health`)
        const data = await res.json()
        if (!res.ok) throw new Error(JSON.stringify(data))
        return { result: "Success", data }
      } else if (input.operation === "registry") {
        const res = await fetch(`${bridgeUrl}/registry`)
        const data = await res.json()
        if (!res.ok) throw new Error(JSON.stringify(data))
        return { result: "Success", data }
      }
    } catch (err: any) {
      return { result: `Error: ${err.message}` }
    }

    return { result: "Unknown operation" }
  },
})
