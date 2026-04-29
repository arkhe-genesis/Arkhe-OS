// @ts-nocheck
/** Public entry point for the neural motion-matching engine.
 *
 *  Typical integration:
 *
 *    import { WebGPURenderer } from "three/examples/jsm/nodes/Nodes";
 *    import { NMMEngine } from "./engine";
 *
 *    const renderer = new WebGPURenderer({
 *      canvas, antialias: true,
 *      requiredLimits: { maxStorageBuffersPerShaderStage: 10 },
 *    });
 *    await renderer.init();
 *
 *    const engine = await NMMEngine.load({
 *      renderer,
 *      bundleBaseUrl: "/",
 *      characterGlbUrl: "/assets/geno.glb",
 *      maxAgents: 32,
 *      bundleKind: "biped",
 *    });
 *    scene.add(engine.mesh);
 *
 *    const agent = engine.createAgent({
 *      position: [0, 0, 0], facing: [0, 0, 1], style: "Neutral",
 *    });
 *
 *    // Per frame:
 *    agent.setGoal(velocity, facing);
 *    engine.update(dt);
 *    renderer.render(scene, camera);
 *
 *  All registered agents share a single batched WebGPU compute dispatch per
 *  prediction tick, so per-agent cost is sublinear in agent count. The
 *  upstream AI4AnimationPy reference is single-character.
 */

export { NMMEngine } from "./NMMEngine";
export type { NMMEngineOptions } from "./NMMEngine";
export { NMMAgent } from "./NMMAgent";
export type { NMMAgentOptions } from "./NMMAgent";
export type { WeightPrecision } from "../inference/Inference";

export type { Vec3 } from "../math/vec3";
export type { Bundle, BundleMeta } from "../model/bundle";
