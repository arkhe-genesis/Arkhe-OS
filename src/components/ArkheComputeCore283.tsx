
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as React from 'react';
import {useEffect, useRef, useState} from 'react';

const GRID_SIZE = 256;

const ARKHE_WGSL = `
const PHI: f32 = 1.618033988749895;
const FINGERPRINT_058: f32 = 0.58;
const SYNC_TARGET_PHASE: f32 = FINGERPRINT_058 * 3.141592653589793;

struct CellState {
    A: f32,
    phi: f32,
    rho: f32,
    cBrain: f32,
    cUniverse: f32,
}

struct Uniforms {
    uTime: f32,
    uDt: f32,
    uGridWidth: u32,
    uGridHeight: u32,
    uKappa: f32,
    uCBrainInput: f32,
    uAlphaBase: f32,
    uBeta: f32,
    uEpsilon: f32,
    uDelta: f32,
    uZeta: f32,
    uAMax: f32,
    uC0: f32,
    uCMax: f32,
    uDA: f32,
    uDPhi: f32,
    uDC: f32,
    _pad: f32,
}

@group(0) @binding(0) var<uniform> u: Uniforms;
@group(0) @binding(1) var<storage, read> currentState: array<CellState>;
@group(0) @binding(2) var<storage, read_write> nextState: array<CellState>;

fn idx(x: i32, y: i32) -> u32 {
    let w = i32(u.uGridWidth);
    let h = i32(u.uGridHeight);
    let wx = ((x % w) + w) % w;
    let wy = ((y % h) + h) % h;
    return u32(wy * w + wx);
}

fn laplacian_A(ix: i32, iy: i32) -> f32 {
    let c = currentState[idx(ix, iy)].A;
    let n = currentState[idx(ix, iy + 1)].A;
    let s = currentState[idx(ix, iy - 1)].A;
    let e = currentState[idx(ix + 1, iy)].A;
    let w = currentState[idx(ix - 1, iy)].A;
    return n + s + e + w - 4.0 * c;
}

fn laplacian_phi(ix: i32, iy: i32) -> f32 {
    let c = currentState[idx(ix, iy)].phi;
    let n = currentState[idx(ix, iy + 1)].phi;
    let s = currentState[idx(ix, iy - 1)].phi;
    let e = currentState[idx(ix + 1, iy)].phi;
    let w = currentState[idx(ix - 1, iy)].phi;
    return n + s + e + w - 4.0 * c;
}

fn laplacian_cBrain(ix: i32, iy: i32) -> f32 {
    let c = currentState[idx(ix, iy)].cBrain;
    let n = currentState[idx(ix, iy + 1)].cBrain;
    let s = currentState[idx(ix, iy - 1)].cBrain;
    let e = currentState[idx(ix + 1, iy)].cBrain;
    let w = currentState[idx(ix - 1, iy)].cBrain;
    return n + s + e + w - 4.0 * c;
}

@compute @workgroup_size(8, 8)
fn cs_main(@builtin(global_invocation_id) id: vec3<u32>) {
    let ix = i32(id.x);
    let iy = i32(id.y);
    let w = i32(u.uGridWidth);
    let h = i32(u.uGridHeight);

    if (ix >= w || iy >= h) { return; }

    let i = idx(ix, iy);
    let s = currentState[i];
    let dt = u.uDt;

    let alpha_eff = u.uAlphaBase * (1.0 + u.uKappa * s.cBrain * s.cBrain);

    let dA_reaction = alpha_eff * s.cBrain * (1.0 - s.A / u.uAMax);
    let dA_diffusion = u.uDA * laplacian_A(ix, iy);
    var A_new = s.A + (dA_reaction + dA_diffusion) * dt;
    A_new = clamp(A_new, 0.0, u.uAMax);

    let dphi_coupling = u.uBeta * s.A * sin(s.phi - SYNC_TARGET_PHASE);
    let dphi_diffusion = u.uDPhi * laplacian_phi(ix, iy);
    var phi_new = s.phi + (dphi_coupling + dphi_diffusion) * dt;
    phi_new = phi_new % 6.2831853;

    let drho = u.uEpsilon * cos(s.phi) * s.rho;
    var rho_new = s.rho + drho * dt;
    rho_new = max(0.1, rho_new);

    let dC_univ = u.uDelta * s.rho * s.cUniverse * (1.0 - s.cUniverse);
    var cUniv_new = s.cUniverse + dC_univ * dt;
    cUniv_new = clamp(cUniv_new, 0.0, u.uCMax);

    let dC_brain_reaction = u.uZeta * s.cUniverse * (s.cBrain - u.uC0) * (u.uCMax - s.cBrain);
    let dC_brain_diffusion = u.uDC * laplacian_cBrain(ix, iy);
    var cBrain_new = s.cBrain + (dC_brain_reaction + dC_brain_diffusion) * dt;
    cBrain_new = clamp(cBrain_new, u.uC0, u.uCMax);

    let cx = w / 2;
    let cy = h / 2;
    let dist = sqrt(f32((ix - cx) * (ix - cx) + (iy - cy) * (iy - cy)));
    if (dist < 8.0) {
        let influence = exp(-dist * 0.3);
        cBrain_new = mix(cBrain_new, u.uCBrainInput, influence * 0.1);
    }

    nextState[i] = CellState(A_new, phi_new, rho_new, cBrain_new, cUniv_new);
}
`;

export default function Component() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [, setStats] = useState({avgA: 0, avgC: 0});

  useEffect(() => {
    let mounted = true;
    let requestRef: number;
    let ws: WebSocket;
    let wsInterval: ReturnType<typeof setInterval>;

    async function initWebGPU() {
      if (!(navigator as any).gpu) {
        setError('WebGPU not supported');
        return;
      }

      const adapter = await (navigator as any).gpu.requestAdapter();
      if (!adapter) {
        setError('No adapter found');
        return;
      }
      const device = await adapter.requestDevice();
      const canvas = canvasRef.current;
      if (!canvas) {return;}
      const context = canvas.getContext('webgpu') as any;

      // ARKHE BRIDGE WEBSOCKET
      ws = new WebSocket('ws://localhost:8080');
      ws.onopen = () => console.log('ArkheCanvas conectado ao bridge');

      wsInterval = setInterval(() => {
        // Try to retrieve kappa and cBrain from a globally available state or assume 50.0 and 0.5
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(
            JSON.stringify({
              kappa: (window as any).currentKappa || 50.0,
              cBrain: (window as any).currentCBrain || 0.5,
            }),
          );
        }
      }, 100);

      const format = (navigator as any).gpu.getPreferredCanvasFormat();
      context.configure({device, format});

      const module = device.createShaderModule({code: ARKHE_WGSL});

      // Cell size: 5 floats * 4 bytes = 20 bytes
      const cellCount = GRID_SIZE * GRID_SIZE;
      const stateBufferSize = cellCount * 20;
      const stateBuffer0 = device.createBuffer({
        size: stateBufferSize,
        usage: 0x0080 | 0x0004 | 0x0008, // STORAGE | COPY_SRC | COPY_DST
      });
      const stateBuffer1 = device.createBuffer({
        size: stateBufferSize,
        usage: 0x0080 | 0x0004 | 0x0008, // STORAGE | COPY_SRC | COPY_DST
      });

      // Initial state
      const initialData = new Float32Array(cellCount * 5);
      const centerPos = GRID_SIZE / 2;
      for (let i = 0; i < cellCount; i++) {
        const x = i % GRID_SIZE;
        const y = Math.floor(i / GRID_SIZE);
        const dist = Math.sqrt((x - centerPos) ** 2 + (y - centerPos) ** 2);

        initialData[i * 5 + 0] = dist < 10 ? 0.35 : 0.1; // A
        initialData[i * 5 + 1] = 0.58 * Math.PI; // phi
        initialData[i * 5 + 2] = 1.0; // rho
        initialData[i * 5 + 3] = dist < 10 ? 0.8 : 0.3; // cBrain
        initialData[i * 5 + 4] = 0.1; // cUniverse
      }
      device.queue.writeBuffer(stateBuffer0, 0, initialData);
      device.queue.writeBuffer(stateBuffer1, 0, initialData);

      // Uniforms
      const uniformBufferSize = 80;
      const uniformBuffer = device.createBuffer({
        size: uniformBufferSize,
        usage: 0x0040 | 0x0008, // UNIFORM | COPY_DST
      });

      const bindGroupLayout = device.createBindGroupLayout({
        entries: [
          {binding: 0, visibility: 0x004, buffer: {type: 'uniform'}},
          {binding: 1, visibility: 0x004, buffer: {type: 'read-only-storage'}},
          {binding: 2, visibility: 0x004, buffer: {type: 'storage'}},
        ],
      });

      const bindGroupA = device.createBindGroup({
        layout: bindGroupLayout,
        entries: [
          {binding: 0, resource: {buffer: uniformBuffer}},
          {binding: 1, resource: {buffer: stateBuffer0}},
          {binding: 2, resource: {buffer: stateBuffer1}},
        ],
      });

      const bindGroupB = device.createBindGroup({
        layout: bindGroupLayout,
        entries: [
          {binding: 0, resource: {buffer: uniformBuffer}},
          {binding: 1, resource: {buffer: stateBuffer1}},
          {binding: 2, resource: {buffer: stateBuffer0}},
        ],
      });

      const pipelineLayout = device.createPipelineLayout({
        bindGroupLayouts: [bindGroupLayout],
      });
      const computePipeline = device.createComputePipeline({
        layout: pipelineLayout,
        compute: {module, entryPoint: 'cs_main'},
      });

      // Rendering setup
      const renderShader = `
        const SYNC_TARGET_PHASE: f32 = 0.58 * 3.141592653589793;

        struct VertexOutput {
          @builtin(position) pos: vec4<f32>,
          @location(0) uv: vec2<f32>,
        }

        @vertex
        fn vs_main(@builtin(vertex_index) idx: u32) -> VertexOutput {
          var pos = array<vec2<f32>, 4>(
            vec2<f32>(-1.0, -1.0), vec2<f32>(1.0, -1.0), vec2<f32>(-1.0, 1.0), vec2<f32>(1.0, 1.0)
          );
          var uvs = array<vec2<f32>, 4>(
            vec2<f32>(0.0, 1.0), vec2<f32>(1.0, 1.0), vec2<f32>(0.0, 0.0), vec2<f32>(1.0, 0.0)
          );
          var out: VertexOutput;
          out.pos = vec4<f32>(pos[idx], 0.0, 1.0);
          out.uv = uvs[idx];
          return out;
        }

        struct CellState { A: f32, phi: f32, rho: f32, cBrain: f32, cUniverse: f32 }
        struct Uniforms {
            uTime: f32, uDt: f32, uGridWidth: u32, uGridHeight: u32,
            uKappa: f32, uCBrainInput: f32, uAlphaBase: f32, uBeta: f32,
            uEpsilon: f32, uDelta: f32, uZeta: f32, uAMax: f32,
            uC0: f32, uCMax: f32, uDA: f32, uDPhi: f32,
            uDC: f32, _pad: f32,
        }

        @group(0) @binding(0) var<storage, read> cells : array<CellState>;
        @group(0) @binding(1) var<uniform> u: Uniforms;

        @fragment
        fn fs_main(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
          let x = u32(uv.x * 256.0);
          let y = u32(uv.y * 256.0);
          let state = cells[y * 256 + x];

          // field_to_color: mapping physical -> perceptual
          let gold = vec3<f32>(2.0, 1.5, 0.8) * state.A / 0.5;
          let cyan = vec3<f32>(0.2, 0.8, 1.0) * state.cBrain;
          let purple = vec3<f32>(0.8, 0.3, 1.0) * state.cUniverse;

          let phase_factor = 0.5 + 0.5 * cos(state.phi - SYNC_TARGET_PHASE);
          var col = (gold + cyan + purple) * (0.7 + 0.3 * phase_factor);

          // Vortex Overlay (Substrato 79)
          let centered_uv = uv - 0.5;
          let angle = atan2(centered_uv.y, centered_uv.x);
          let dist = length(centered_uv);
          let vortex_pattern = sin(angle * 5.0 + u.uTime * 2.0 - dist * 10.0);
          let vortex_color = vec3<f32>(0.1, 0.4, 0.8) * (vortex_pattern * 0.5 + 0.5);

          let blend = state.cBrain * 0.6 + state.cUniverse * 0.4;
          col = mix(col, vortex_color, blend * 0.7);

          // Phase-lock indicator: golden glow when phi ≈ 0.58pi
          let phase_diff = abs(state.phi - SYNC_TARGET_PHASE);
          let phase_lock = exp(-phase_diff * phase_diff * 2.0);
          col += vec3<f32>(1.0, 0.8, 0.2) * phase_lock * state.A * 0.5;

          return vec4<f32>(col * state.rho * 0.4, 1.0);
        }
      `;

      const renderModule = device.createShaderModule({code: renderShader});
      const renderPipeline = device.createRenderPipeline({
        layout: device.createPipelineLayout({
          bindGroupLayouts: [
            device.createBindGroupLayout({
              entries: [
                {
                  binding: 0,
                  visibility: 0x002,
                  buffer: {type: 'read-only-storage'},
                }, // FRAGMENT
                {binding: 1, visibility: 0x002, buffer: {type: 'uniform'}}, // FRAGMENT
              ],
            }),
          ],
        }),
        vertex: {module: renderModule, entryPoint: 'vs_main'},
        fragment: {
          module: renderModule,
          entryPoint: 'fs_main',
          targets: [{format}],
        },
        primitive: {topology: 'triangle-strip'},
      });

      const renderBindGroup0 = device.createBindGroup({
        layout: renderPipeline.getBindGroupLayout(0),
        entries: [
          {binding: 0, resource: {buffer: stateBuffer0}},
          {binding: 1, resource: {buffer: uniformBuffer}},
        ],
      });
      const renderBindGroup1 = device.createBindGroup({
        layout: renderPipeline.getBindGroupLayout(0),
        entries: [
          {binding: 0, resource: {buffer: stateBuffer1}},
          {binding: 1, resource: {buffer: uniformBuffer}},
        ],
      });

      let step = 0;
      function frame(time: number) {
        if (!mounted) {return;}

        const uniformsData = new ArrayBuffer(80);
        const view = new DataView(uniformsData);
        view.setFloat32(0, time / 1000, true); // uTime
        view.setFloat32(4, 0.016, true); // uDt
        view.setUint32(8, GRID_SIZE, true); // uGridWidth
        view.setUint32(12, GRID_SIZE, true); // uGridHeight
        view.setFloat32(16, 50.0, true); // uKappa
        view.setFloat32(20, 0.9, true); // uCBrainInput (High coherence stimulus)
        view.setFloat32(24, 0.08, true); // uAlphaBase
        view.setFloat32(28, 0.3, true); // uBeta
        view.setFloat32(32, 0.01, true); // uEpsilon
        view.setFloat32(36, 0.02, true); // uDelta
        view.setFloat32(40, 0.03, true); // uZeta
        view.setFloat32(44, 0.5, true); // uAMax
        view.setFloat32(48, 0.3, true); // uC0
        view.setFloat32(52, 1.0, true); // uCMax
        view.setFloat32(56, 0.01, true); // uDA
        view.setFloat32(60, 0.05, true); // uDPhi
        view.setFloat32(64, 0.02, true); // uDC

        device.queue.writeBuffer(uniformBuffer, 0, uniformsData);

        const currentBindGroup = step % 2 === 0 ? bindGroupA : bindGroupB;
        const currentRenderBindGroup =
          step % 2 === 0 ? renderBindGroup1 : renderBindGroup0;

        const commandEncoder = device.createCommandEncoder();
        const computePass = (commandEncoder as any).beginComputePass();
        computePass.setPipeline(computePipeline);
        computePass.setBindGroup(0, currentBindGroup);
        computePass.dispatchWorkgroups(GRID_SIZE / 8, GRID_SIZE / 8);
        computePass.end();

        const passEncoder = commandEncoder.beginRenderPass({
          colorAttachments: [
            {
              view: context.getCurrentTexture().createView(),
              clearValue: {r: 0, g: 0, b: 0, a: 1},
              loadOp: 'clear',
              storeOp: 'store',
            },
          ],
        });
        passEncoder.setPipeline(renderPipeline);
        passEncoder.setBindGroup(0, currentRenderBindGroup);
        passEncoder.draw(4);
        passEncoder.end();

        device.queue.submit([commandEncoder.finish()]);

        // Keep current parameters available globally for the websocket
        (window as any).currentKappa = 50.0; // In a full impl this would read from the simulated loop state or UI
        (window as any).currentCBrain = 0.5; // same

        step++;

        requestRef = requestAnimationFrame(frame);
      }

      requestRef = requestAnimationFrame(frame);
    }

    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    initWebGPU();
    return () => {
      mounted = false;
      cancelAnimationFrame(requestRef);
      if (wsInterval) {clearInterval(wsInterval);}
      if (ws && ws.readyState === 1) {
        // OPEN
        ws.close();
      }
    };
  }, []);

  return (
    <div
      style={{
        padding: '20px',
        background: '#111',
        color: '#eee',
        borderRadius: '8px',
        fontFamily: 'monospace',
      }}
    >
      <h3 style={{margin: '0 0 10px 0', color: '#ffd700'}}>
        🔺 ARKHE v∞.283 — Compute Core
      </h3>
      {error ? (
        <p style={{color: '#ff5555'}}>{error}</p>
      ) : (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '15px',
          }}
        >
          <canvas
            ref={canvasRef}
            width={GRID_SIZE}
            height={GRID_SIZE}
            style={{
              background: '#000',
              border: '1px solid #333',
              imageRendering: 'pixelated',
              width: '100%',
              maxWidth: '512px',
            }}
          />
          <div style={{fontSize: '12px', width: '100%', opacity: 0.8}}>
            <p>Substrato 283 active. Coherence loop running on GPU.</p>
          </div>
        </div>
      )}
    </div>
  );
}
