/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useRef, useEffect, useState } from 'react';
import { X, Activity, Shield, Network, Eye, MousePointer2 } from 'lucide-react';

const VERTEX_SHADER = `#version 300 es
in vec4 a_position;
void main() {
    gl_Position = a_position;
}
`;

const FRAGMENT_SHADER = `#version 300 es
precision highp float;
out vec4 fragColor;

uniform vec2 iResolution;
uniform float iTime;

#define MAX_NODES 10
#define MAX_EDGES 10

uniform vec3 uNodePositions[MAX_NODES];
uniform vec4 uNodeColors[MAX_NODES];
uniform float uNodeSizes[MAX_NODES];
uniform int uNodeSecurityStates[MAX_NODES];
uniform int uNodeCount;

uniform ivec2 uEdges[MAX_EDGES];
uniform int uEdgeCount;

#define MAX_STEPS 100
#define SURF_DIST 0.01
#define MAX_DIST 100.0

float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 ab = b - a;
    vec3 ap = p - a;
    float t = dot(ap, ab) / dot(ab, ab);
    t = clamp(t, 0.0, 1.0);
    vec3 c = a + t * ab;
    return length(p - c) - r;
}

float mapScene(vec3 p, out vec3 color, out int securityState) {
    float d = MAX_DIST;
    color = vec3(0.02, 0.02, 0.05);
    securityState = 0;

    // Render Nodes
    for(int i = 0; i < uNodeCount; i++) {
        float size = uNodeSizes[i];
        int sState = uNodeSecurityStates[i];

        if (sState == 2) {
            size += sin(p.x * 20.0 + iTime * 10.0) * 0.05;
        } else if (sState == 1) {
            size += sin(iTime * 5.0) * 0.02;
        }

        float ds = sdSphere(p - uNodePositions[i], size);
        if (ds < d) {
            d = ds;
            color = uNodeColors[i].rgb;
            securityState = sState;
        }
    }

    // Render Edges
    for(int i = 0; i < uEdgeCount; i++) {
        if (i >= uEdgeCount) break;
        vec3 a = uNodePositions[uEdges[i].x];
        vec3 b = uNodePositions[uEdges[i].y];
        float de = sdCapsule(p, a, b, 0.02);
        if (de < d) {
            d = de;
            color = vec3(0.3, 0.3, 0.4);
            securityState = 0;
        }
    }

    return d;
}

vec3 getNormal(vec3 p) {
    vec3 color;
    int sState;
    float d = mapScene(p, color, sState);
    vec2 e = vec2(0.01, 0);
    vec3 n = d - vec3(
        mapScene(p - e.xyy, color, sState),
        mapScene(p - e.yxy, color, sState),
        mapScene(p - e.yyx, color, sState)
    );
    return normalize(n);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution.xy) / iResolution.y;

    float angle = iTime * 0.1;
    mat3 rot = mat3(
        cos(angle), 0, sin(angle),
        0, 1, 0,
        -sin(angle), 0, cos(angle)
    );

    vec3 ro = rot * vec3(0, 1, -6);
    vec3 rd = rot * normalize(vec3(uv, 1.2));

    float dO = 0.0;
    vec3 finalColor = vec3(0.01, 0.01, 0.02);

    for(int i = 0; i < MAX_STEPS; i++) {
        vec3 p = ro + rd * dO;
        vec3 tempColor;
        int tempState;
        float dS = mapScene(p, tempColor, tempState);
        dO += dS;
        if (dS < SURF_DIST) {
            vec3 n = getNormal(p);
            vec3 lightDir = normalize(vec3(1, 2, -3));
            float diff = max(dot(n, lightDir), 0.1);
            finalColor = tempColor * diff;

            if (tempState == 2) {
                float pulse = 0.5 + 0.5 * sin(iTime * 10.0);
                finalColor = mix(finalColor, vec3(1, 0.2, 0), pulse);
            } else if (tempState == 1) {
                float pulse = 0.8 + 0.2 * sin(iTime * 5.0);
                finalColor *= pulse;
            }

            finalColor += tempColor * 0.2;
            break;
        }
        if (dO > MAX_DIST) break;
    }

    finalColor = mix(finalColor, vec3(0, 0, 0.05), 1.0 - exp(-0.02 * dO));
    fragColor = vec4(finalColor, 1.0);
}
`;

interface NodeData {
    uri: string;
    position: [number, number, number];
    color: [number, number, number, number];
    size: number;
    type: number;
    securityState: number;
}

interface EdgeData {
    sourceIndex: number;
    targetIndex: number;
    relationType: number;
    strength: number;
}

export default function ArkheOntologyVision({ onClose }: { onClose: () => void }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [nodes, setNodes] = useState<NodeData[]>([]);
    const [edges, setEdges] = useState<EdgeData[]>([]);
    const [sessionId] = useState(() => Math.random().toString(36).substring(7));
    const requestRef = useRef<number>(0);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/visualization-state');
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();
                setNodes(data.nodes);
                setEdges(data.edges);
            } catch (error) {
                console.error("Failed to fetch visualization state:", error);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    // Automated Telemetry Stream
    useEffect(() => {
        const sendTelemetry = async () => {
            const time = performance.now() * 0.001;
            const angle = time * 0.1;

            // Camera position/direction (simplified for demonstration)
            const pos = {
                x: 6 * Math.sin(angle),
                y: 1,
                z: -6 * Math.cos(angle)
            };
            const dir = {
                x: -Math.sin(angle),
                y: 0,
                z: Math.cos(angle)
            };

            const telemetry = {
                session_id: sessionId,
                timestamp: new Date().toISOString(),
                viewport: { position: pos, direction: dir },
                rendering_metrics: { fps: 60 }
            };

            try {
                await fetch('/api/visual-telemetry', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(telemetry)
                });
            } catch (err) {
                // Fail silently in telemetry
            }
        };

        const interval = setInterval(sendTelemetry, 1000);
        return () => clearInterval(interval);
    }, [sessionId]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const gl = canvas.getContext('webgl2');
        if (!gl) return;

        const createShader = (gl: WebGL2RenderingContext, type: number, source: string) => {
            const shader = gl.createShader(type)!;
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            return shader;
        };

        const program = gl.createProgram()!;
        gl.attachShader(program, createShader(gl, gl.VERTEX_SHADER, VERTEX_SHADER));
        gl.attachShader(program, createShader(gl, gl.FRAGMENT_SHADER, FRAGMENT_SHADER));
        gl.linkProgram(program);
        gl.useProgram(program);

        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
        const posLoc = gl.getAttribLocation(program, 'a_position');
        gl.enableVertexAttribArray(posLoc);
        gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

        const resLoc = gl.getUniformLocation(program, 'iResolution');
        const timeLoc = gl.getUniformLocation(program, 'iTime');
        const nodePosLoc = gl.getUniformLocation(program, 'uNodePositions');
        const nodeColLoc = gl.getUniformLocation(program, 'uNodeColors');
        const nodeSizeLoc = gl.getUniformLocation(program, 'uNodeSizes');
        const nodeSecLoc = gl.getUniformLocation(program, 'uNodeSecurityStates');
        const nodeCountLoc = gl.getUniformLocation(program, 'uNodeCount');
        const edgeLoc = gl.getUniformLocation(program, 'uEdges');
        const edgeCountLoc = gl.getUniformLocation(program, 'uEdgeCount');

        const render = (time: number) => {
            if (!canvasRef.current) return;
            gl.viewport(0, 0, canvas.width, canvas.height);
            gl.uniform2f(resLoc, canvas.width, canvas.height);
            gl.uniform1f(timeLoc, time * 0.001);

            if (nodes.length > 0) {
                const nodeLimit = Math.min(nodes.length, 10);
                gl.uniform3fv(nodePosLoc, new Float32Array(nodes.slice(0, nodeLimit).flatMap(n => n.position)));
                gl.uniform4fv(nodeColLoc, new Float32Array(nodes.slice(0, nodeLimit).flatMap(n => n.color)));
                gl.uniform1fv(nodeSizeLoc, new Float32Array(nodes.slice(0, nodeLimit).map(n => n.size)));
                gl.uniform1iv(nodeSecLoc, new Int32Array(nodes.slice(0, nodeLimit).map(n => n.securityState)));
                gl.uniform1i(nodeCountLoc, nodeLimit);
            }

            if (edges.length > 0) {
                const edgeLimit = Math.min(edges.length, 10);
                gl.uniform2iv(edgeLoc, new Int32Array(edges.slice(0, edgeLimit).flatMap(e => [e.sourceIndex, e.targetIndex])));
                gl.uniform1i(edgeCountLoc, edgeLimit);
            }

            gl.drawArrays(gl.TRIANGLES, 0, 6);
            requestRef.current = requestAnimationFrame(render);
        };

        requestRef.current = requestAnimationFrame(render);
        return () => cancelAnimationFrame(requestRef.current);
    }, [nodes, edges]);

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 backdrop-blur-md p-4">
            <div className="w-full max-w-7xl bg-[#0a0a0c] border border-cyan-500/30 rounded-2xl shadow-[0_0_50px_rgba(0,255,170,0.2)] overflow-hidden flex flex-col h-[90vh]">
                <div className="flex items-center justify-between p-6 border-b border-cyan-500/20 bg-cyan-500/5">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-cyan-500/10 rounded-xl border border-cyan-500/30">
                            <Eye className="w-8 h-8 text-cyan-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-cyan-400 tracking-[0.2em] uppercase font-mono">Immersive Telemetry HUD</h2>
                            <div className="text-xs font-mono text-cyan-500/60 flex items-center gap-2">
                                <Activity className="w-4 h-4 text-emerald-400" />
                                Monitoramento Passivo de Infraestrutura Crítica
                            </div>
                        </div>
                    </div>
                    <button onClick={onClose} className="group flex items-center gap-2 px-4 py-2 border border-white/10 rounded-lg text-neutral-500 hover:text-white hover:border-white transition-all">
                        <span className="text-xs font-mono uppercase tracking-widest">DISCONNECT_SESSION [ESC]</span>
                        <X className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                    </button>
                </div>

                <div className="flex-1 relative flex flex-col lg:flex-row overflow-hidden">
                    <div className="flex-1 relative bg-black">
                        <canvas
                            ref={canvasRef}
                            width={1600}
                            height={900}
                            className="w-full h-full object-cover"
                        />

                        <div className="absolute top-6 left-6 flex flex-col gap-3">
                            <div className="flex items-center gap-3 px-4 py-2 bg-black/60 border border-emerald-500/30 rounded-lg backdrop-blur-md">
                                <Shield className="w-4 h-4 text-emerald-400" />
                                <span className="text-[10px] font-mono text-white uppercase tracking-widest">Auditoria Assistida: ATIVA</span>
                            </div>
                            <div className="flex items-center gap-3 px-4 py-2 bg-black/60 border border-cyan-500/30 rounded-lg backdrop-blur-md">
                                <Activity className="w-4 h-4 text-cyan-400" />
                                <span className="text-[10px] font-mono text-white uppercase tracking-widest">Sessão: {sessionId}</span>
                            </div>
                        </div>
                    </div>

                    <div className="w-full lg:w-96 bg-[#050507] border-l border-white/10 p-6 flex flex-col gap-6 overflow-y-auto">
                        <h3 className="font-mono text-xs uppercase tracking-[0.2em] text-neutral-500 border-b border-white/10 pb-3 flex items-center gap-2">
                            <Activity className="w-4 h-4" /> Telemetria Visual (Read-Only)
                        </h3>

                        <div className="space-y-4">
                            {nodes.map((node, i) => (
                                <div key={i} className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-[10px] font-mono text-neutral-500">OBJECT_{i.toString().padStart(2, '0')}</span>
                                        <div className="text-[8px] font-mono text-cyan-400 bg-cyan-400/10 px-2 py-0.5 rounded">MAP_SYNC_OK</div>
                                    </div>
                                    <p className="text-[9px] font-mono text-neutral-500 leading-tight">
                                        Coord: [{node.position.map(p => p.toFixed(2)).join(', ')}]
                                    </p>
                                </div>
                            ))}
                        </div>

                        <div className="mt-auto p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl">
                            <p className="text-[10px] font-mono text-blue-400 uppercase mb-2 font-bold">Modo de Navegação</p>
                            <p className="text-[9px] font-mono text-neutral-500 leading-relaxed">
                                Você está em modo de inspeção passiva. Seus movimentos de câmera e tempos de permanência são correlacionados no backend para detecção de anomalias semânticas.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
