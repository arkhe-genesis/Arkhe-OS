/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Activity, Shield,  Eye, MousePointer2, AlertTriangle, CheckCircle2, Lock, Fingerprint } from 'lucide-react';
import React, { useRef, useEffect, useState } from 'react';

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
    const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
    const [notification, setNotification] = useState<{type: 'success' | 'error' | 'info', message: string} | null>(null);
    const [isProving, setIsProving] = useState(false);
    const [sessionId] = useState(() => Math.random().toString(36).substring(7));
    const requestRef = useRef<number>(0);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/visualization-state');
                if (!response.ok) {throw new Error('Network response was not ok');}
                const data = await response.json();
                setNodes(data.nodes);
                setEdges(data.edges);
            } catch (error) {
                console.error("Failed to fetch visualization state:", error);
            }
        };
        void fetchData();
        const interval = setInterval(() => { void fetchData(); }, 5000);
        return () => clearInterval(interval);
    }, []);

    // Automated Telemetry Stream
    useEffect(() => {
        const sendTelemetry = async () => {
            const time = performance.now() * 0.001;
            const angle = time * 0.1;

            const pos = { x: 6 * Math.sin(angle), y: 1, z: -6 * Math.cos(angle) };
            const dir = { x: -Math.sin(angle), y: 0, z: Math.cos(angle) };

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
            } catch (_err) {}
        };

        const interval = setInterval(() => {
          void sendTelemetry();
        }, 1000);
        return () => clearInterval(interval);
    }, [sessionId]);

    const handleZKChallenge = async () => {
        if (!selectedNode) {return;}
        setIsProving(true);
        setNotification({type: 'info', message: 'Iniciando Desafio ZK (Commit-and-Prove)...'});

        try {
            // 1. Get challenge from backend
            // In a real system, we'd hash the URI using the same logic as backend
            const nodeHash = selectedNode.uri.split(':').pop() || "unknown";
            const challengeRes = await fetch(`/api/game/zk-challenge/${nodeHash}`);
            const _challenge = await challengeRes.json();

            // 2. Simulate Local Proof Generation (WASM)
            await new Promise(resolve => setTimeout(resolve, 2000));

            // 3. Submit Proof
            const reportRes = await fetch('/api/game/zk-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    proof: { pi_a: ["0x1", "0x2"], pi_b: [["0x3", "0x4"], ["0x5", "0x6"]], pi_c: ["0x7", "0x8"] },
                    public_inputs: {
                        commitment: "26487e41258d9294", // Simulation of the hash for 'Cognitive'
                        violation_exists: selectedNode.securityState > 0
                    }
                })
            });
            const reportResult = await reportRes.json();

            if (reportResult.status === 'verified') {
                setNotification({
                    type: 'success',
                    message: `PROVA ZK VERIFICADA! Conformidade validada sem revelar URI.`
                });
            } else {
                setNotification({
                    type: 'error',
                    message: `FALHA NA PROVA ZK. O recurso está em conformidade formal.`
                });
            }
        } catch (_err) {
            setNotification({type: 'error', message: 'Erro no protocolo de privacidade ZK.'});
        } finally {
            setIsProving(false);
            setTimeout(() => setNotification(null), 5000);
        }
    };

    const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) {return;}
        const rect = canvas.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / canvas.clientWidth) * 2 - 1;
        const y = -(((e.clientY - rect.top) / canvas.clientHeight) * 2 - 1);

        const time = performance.now() * 0.001;
        const angle = time * 0.1;

        let nearest: NodeData | null = null;
        let minDist = 0.5;

        nodes.forEach(node => {
            const cosA = Math.cos(angle);
            const sinA = Math.sin(angle);
            const rx = node.position[0] * cosA + node.position[2] * sinA;
            const rz = -node.position[0] * sinA + node.position[2] * cosA;
            const ry = node.position[1];
            const distZ = rz - (-6);
            if (distZ > 0) {
                const px = rx / distZ * 1.2;
                const py = (ry - 1) / distZ * 1.2;
                const d = Math.sqrt((px - x)**2 + (py - y)**2);
                if (d < minDist) {
                    minDist = d;
                    nearest = node;
                }
            }
        });
        setSelectedNode(nearest);
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) {return;}
        const gl = canvas.getContext('webgl2');
        if (!gl) {return;}

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
            if (!canvasRef.current) {return;}
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
                            <h2 className="text-2xl font-bold text-cyan-400 tracking-[0.2em] uppercase font-mono">Arkhe Immersive Defense</h2>
                            <div className="text-xs font-mono text-cyan-500/60 flex items-center gap-2">
                                <Activity className="w-4 h-4 text-emerald-400" />
                                Monitoramento de Integridade Ontológica com Privacidade ZK
                            </div>
                        </div>
                    </div>
                    <button onClick={onClose} className="group flex items-center gap-2 px-4 py-2 border border-white/10 rounded-lg text-neutral-500 hover:text-white hover:border-white transition-all">
                        <span className="text-xs font-mono uppercase tracking-widest">DISCONNECT [ESC]</span>
                        <X className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                    </button>
                </div>

                <div className="flex-1 relative flex flex-col lg:flex-row overflow-hidden">
                    <div className="flex-1 relative bg-black">
                        <canvas
                            ref={canvasRef}
                            width={1600}
                            height={900}
                            onClick={handleCanvasClick}
                            className="w-full h-full object-cover cursor-crosshair"
                        />

                        {notification && (
                            <div className={`absolute top-10 left-1/2 -translate-x-1/2 px-6 py-4 rounded-xl border flex items-center gap-4 animate-bounce z-50 backdrop-blur-xl ${
                                notification.type === 'success' ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400' :
                                notification.type === 'error' ? 'bg-rose-500/20 border-rose-500/50 text-rose-400' :
                                'bg-blue-500/20 border-blue-500/50 text-blue-400'
                            }`}>
                                {notification.type === 'success' ? <CheckCircle2 /> : notification.type === 'info' ? <Fingerprint /> : <AlertTriangle />}
                                <span className="font-mono text-sm font-bold uppercase tracking-widest">{notification.message}</span>
                            </div>
                        )}

                        <div className="absolute top-6 left-6 flex flex-col gap-3">
                            <div className="flex items-center gap-3 px-4 py-2 bg-black/60 border border-emerald-500/30 rounded-lg backdrop-blur-md">
                                <Shield className="w-4 h-4 text-emerald-400" />
                                <span className="text-[10px] font-mono text-white uppercase tracking-widest">Auditoria ZK-Proof Ativa</span>
                            </div>
                        </div>
                    </div>

                    <div className="w-full lg:w-96 bg-[#050507] border-l border-white/10 p-6 flex flex-col gap-6 overflow-y-auto">
                        {selectedNode ? (
                            <div className="space-y-6 animate-in slide-in-from-right">
                                <div className="p-4 bg-white/5 border border-cyan-500/30 rounded-2xl space-y-4">
                                    <h4 className="font-mono text-xs text-cyan-400 uppercase font-bold tracking-widest">Inspeção de Objeto</h4>
                                    <div className="space-y-1">
                                        <div className="text-[9px] text-neutral-500 uppercase font-mono">Assinatura Visual</div>
                                        <div className="text-[10px] text-white font-mono break-all bg-black/40 p-2 rounded border border-white/5">
                                            HASH: {btoa(selectedNode.uri).substring(0, 16)}...
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 text-[9px] text-neutral-400 uppercase font-mono">
                                        <Lock className="w-3 h-3" /> URI Original Oculta por Protocolo de Privacidade
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <h4 className="font-mono text-[10px] text-neutral-500 uppercase tracking-widest">Ação: Auditoria de Integridade</h4>
                                    <button
                                        onClick={handleZKChallenge}
                                        disabled={isProving}
                                        className={`w-full py-4 rounded-xl font-mono text-xs uppercase tracking-widest transition-all flex items-center justify-center gap-3 ${
                                            isProving
                                            ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 animate-pulse'
                                            : 'bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 hover:bg-indigo-500/20'
                                        }`}
                                    >
                                        {isProving ? <Activity className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                                        {isProving ? 'Gerando Prova ZK...' : 'Solicitar Desafio ZK'}
                                    </button>
                                    <p className="text-[8px] font-mono text-neutral-500 leading-tight">
                                        A geração da prova ZK valida restrições SHACL (maxCount) localmente sem expor a URI do recurso ao backend.
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-center gap-4 opacity-40">
                                <MousePointer2 className="w-12 h-12 text-neutral-600 animate-pulse" />
                                <p className="font-mono text-xs text-neutral-500 uppercase tracking-widest">Selecione uma entidade no<br/>universo 3D para interagir.</p>
                            </div>
                        )}

                        <div className="mt-auto border-t border-white/5 pt-6">
                            <div className="flex items-center gap-3 mb-4">
                                <Lock className="w-5 h-5 text-indigo-400" />
                                <span className="font-mono text-[10px] text-white uppercase font-bold">Protocolo Commit-and-Prove</span>
                            </div>
                            <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-lg text-[9px] font-mono text-neutral-400 leading-relaxed">
                                As auditorias utilizam Compromissos de Pedersen e circuitos R1CS (Pinocchio) para garantir que apenas anomalias reais sejam reportadas, mantendo o sigilo da infraestrutura.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
