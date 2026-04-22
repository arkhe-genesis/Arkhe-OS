/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Activity, Cpu, Shield, Search, Info, Settings2 } from 'lucide-react';
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

// Telemetry Uniforms (Moduláveis por Arkhe)
uniform float uWaferDefectRate;
uniform float uOxideThickness;
uniform float uDopingConcentration;
uniform float uAlignmentError;
uniform float uEtchDepth;

// ============================================================================
// UTILITÁRIOS SDF E RUÍDO
// ============================================================================

// Ruído de Voronoi (para simular grãos de cristal e defeitos)
float voronoi(vec2 p, float scale) {
    vec2 i = floor(p * scale);
    vec2 f = fract(p * scale);
    float minDist = 1.0;
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 neighbor = vec2(float(x), float(y));
            vec2 point = vec2(
                sin(dot(i + neighbor, vec2(12.9898, 78.233))) * 43758.5453,
                cos(dot(i + neighbor, vec2(39.346, 11.487))) * 43758.5453
            );
            point = 0.5 + 0.5 * fract(point);
            vec2 diff = neighbor + point - f;
            float dist = length(diff);
            minDist = min(minDist, dist);
        }
    }
    return minDist;
}

// Ruído de Perlin 3D (para simular textura de óxido)
float noise(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    f = f*f*(3.0-2.0*f);
    float n = mix(
        mix(mix(dot(sin(i*2.0), cos(i*3.0)), dot(sin((i+vec3(1,0,0))*2.0), cos((i+vec3(1,0,0))*3.0)), f.x),
            mix(dot(sin((i+vec3(0,1,0))*2.0), cos((i+vec3(0,1,0))*3.0)), dot(sin((i+vec3(1,1,0))*2.0), cos((i+vec3(1,1,0))*3.0)), f.x), f.y),
        mix(mix(dot(sin((i+vec3(0,0,1))*2.0), cos((i+vec3(0,0,1))*3.0)), dot(sin((i+vec3(1,0,1))*2.0), cos((i+vec3(1,0,1))*3.0)), f.x),
            mix(dot(sin((i+vec3(0,1,1))*2.0), cos((i+vec3(0,1,1))*3.0)), dot(sin((i+vec3(1,1,1))*2.0), cos((i+vec3(1,1,1))*3.0)), f.x), f.y), f.z);
    return n * 0.5 + 0.5;
}

// ============================================================================
// ONTOLOGIA VISUAL: O CHIP
// ============================================================================

// 1. O SUBSTRATO (WAFER DE SILÍCIO)
vec3 drawWafer(vec2 uv, vec2 center, float radius) {
    vec2 p = uv - center;
    float dist = length(p) - radius;

    // Borda do wafer (chanfro)
    float waferMask = smoothstep(0.01, 0.0, dist);
    if (waferMask < 0.01) return vec3(0.0);

    // Padrão de rede cristalina (cúbica de diamante)
    float crystal = voronoi(p * 4.0, 20.0);
    crystal = pow(crystal, 2.0);

    // Cor base do silício (cinza-azulado com reflexo especular)
    vec3 siColor = mix(vec3(0.3, 0.35, 0.45), vec3(0.6, 0.65, 0.75), crystal);

    // Reflexo Fresnel (bordas mais brilhantes)
    float fresnel = pow(1.0 - abs(dist), 3.0);
    siColor += vec3(0.8, 0.85, 1.0) * fresnel * 0.5;

    return siColor;
}

// 2. CAMADA DE ÓXIDO (VÉU DE FERRUGEM)
vec3 drawOxide(vec2 uv, vec2 center, float radius, float thickness) {
    vec2 p = uv - center;
    float dist = length(p) - radius;

    // A camada de óxido existe apenas dentro do wafer
    if (dist > 0.0) return vec3(0.0);

    // Efeito de interferência de filme fino (bolha de sabão)
    float oxideNoise = noise(vec3(p * 8.0, iTime * 0.1));
    float interference = sin(dist * 50.0 + oxideNoise * 10.0) * 0.5 + 0.5;

    // Cor do óxido (âmbar/esverdeado, típico de SiO₂)
    vec3 oxideColor = mix(vec3(0.8, 0.7, 0.5), vec3(0.5, 0.6, 0.4), interference);

    // Transparência baseada na espessura
    float alpha = thickness * 0.8;

    return oxideColor * alpha;
}

// 3. MÁSCARA DE LITOGRAFIA (PADRÃO DE CIRCUITO)
float drawCircuitMask(vec2 uv, float scale) {
    vec2 p = uv * scale;

    // Cria um padrão de linhas retas (horizontal, vertical, diagonal)
    float lines = 0.0;

    // Linhas horizontais e verticais
    float gridX = fract(p.x * 0.5);
    float gridY = fract(p.y * 0.5);
    lines += step(0.95, gridX) * step(0.9, fract(p.y * 2.0));
    lines += step(0.95, gridY) * step(0.9, fract(p.x * 2.0));

    // Linhas diagonais (ângulo de 45°)
    float diag = fract((p.x + p.y) * 0.707);
    lines += step(0.95, diag) * 0.5;

    // "Vias" (pequenos círculos de conexão entre camadas)
    vec2 viaPos = floor(p * 2.0) / 2.0;
    float via = length(fract(p * 2.0) - 0.5) - 0.1;
    lines += step(via, 0.0) * 0.8;

    return clamp(lines, 0.0, 1.0);
}

// 4. DOPAGEM (VENENO SAGRADO)
vec3 drawDoping(vec2 uv, vec2 center, float radius) {
    vec2 p = uv - center;
    float dist = length(p) - radius;

    // A dopagem ocorre em regiões específicas (simuladas por ruído)
    float dopingMask = noise(vec3(p * 3.0, iTime * 0.2));
    dopingMask = step(0.6, dopingMask);

    if (dopingMask < 0.5 || dist > 0.0) return vec3(0.0);

    // Tipo de dopante: alterna entre Boro (azul) e Fósforo (vermelho)
    float typeSelector = noise(vec3(p * 2.0, 1.0));
    vec3 dopantColor = mix(vec3(0.2, 0.4, 1.0), vec3(1.0, 0.3, 0.2), step(0.5, typeSelector));

    // Concentração de dopante (brilho)
    float concentration = noise(vec3(p * 10.0, iTime));

    return dopantColor * concentration * 0.8;
}

// 5. ETCHING (CINZEL DE PLASMA) - SDF de subtração
float applyEtching(float dist, vec2 uv, float depth) {
    // O etching remove material onde a máscara NÃO protege
    float mask = drawCircuitMask(uv, 4.0);

    // Onde a máscara está "escura" (0), o material é removido (cria um buraco)
    float etchDepth = (1.0 - mask) * depth;

    // Adiciona rugosidade de plasma (ruído)
    float plasmaRough = noise(vec3(uv * 20.0, iTime));
    etchDepth += plasmaRough * 0.01;

    return dist + etchDepth;
}

// 6. METALIZAÇÃO (CHUVA DE ESTRELAS)
vec3 drawMetallization(vec2 uv, vec2 center, float radius) {
    vec2 p = uv - center;
    float dist = length(p) - radius;

    if (dist > 0.0) return vec3(0.0);

    // A metalização segue o padrão do circuito (apenas onde há máscara)
    float mask = drawCircuitMask(uv, 4.0);
    if (mask < 0.5) return vec3(0.0);

    // Cor do metal (cobre/dourado)
    vec3 metalColor = vec3(1.0, 0.843, 0.0); // Ouro

    // Brilho especular (condutor)
    float shine = pow(mask, 2.0);

    return metalColor * shine;
}

// 7. INSPEÇÃO (OLHO DO GUARDIÃO) - Scanner linear
vec3 drawInspection(vec2 uv, vec2 center, float radius, float defectRate) {
    vec2 p = uv - center;

    // Scanner: uma linha vertical que se move
    float scanPos = fract(iTime * 0.1) * 2.0 - 1.0;
    float scanLine = smoothstep(0.02, 0.0, abs(p.x - scanPos));

    if (scanLine < 0.01) return vec3(0.0);

    // "Pontos quentes" (defeitos) que o scanner revela
    float defect = voronoi(p * 8.0, 15.0);
    defect = step(1.0 - defectRate, defect);

    // Scanner emite luz verde (laser) e defeitos brilham em vermelho
    vec3 scanColor = mix(vec3(0.0, 1.0, 0.0), vec3(1.0, 0.0, 0.0), defect);

    return scanColor * scanLine * 0.8;
}

void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy;
    vec2 center = vec2(0.5, 0.5);
    float radius = 0.4;

    // Camada 1: Substrato de Silício
    vec3 color = drawWafer(uv, center, radius);

    // Camada 2: Óxido (Véu de Ferrugem)
    vec3 oxide = drawOxide(uv, center, radius, uOxideThickness);
    color = mix(color, color + oxide, 0.8);

    // Camada 3: Aplicar Etching (esculpir o circuito)
    vec2 p = uv - center;
    float dist = length(p) - radius;
    // uAlignmentError desloca a máscara
    float etchedDist = applyEtching(dist, uv + uAlignmentError, uEtchDepth);
    float etchMask = smoothstep(0.0, 0.01, etchedDist);

    // Camada 4: Dopagem (brilha nas regiões esculpidas)
    vec3 doping = drawDoping(uv, center, radius) * uDopingConcentration;
    color += doping * (1.0 - etchMask);

    // Camada 5: Metalização (trilhas condutoras)
    vec3 metal = drawMetallization(uv + uAlignmentError, center, radius);
    color = mix(color, metal, 0.9);

    // Camada 6: Inspeção (scanner)
    vec3 inspection = drawInspection(uv, center, radius, uWaferDefectRate);
    color += inspection;

    // Vinheta (escurece as bordas)
    float vignette = 1.0 - length(uv - 0.5) * 0.5;
    color *= vignette;

    fragColor = vec4(color, 1.0);
}
`;

export default function ChipFabricationVision({ onClose }: { onClose: () => void }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [telemetry, setTelemetry] = useState({
        waferDefectRate: 0.05,
        oxideThickness: 0.6,
        dopingConcentration: 1.0,
        alignmentError: 0.0,
        etchDepth: 0.05
    });
    const requestRef = useRef<number>(0);

    useEffect(() => {
        const fetchTelemetry = async () => {
            try {
                // Simulação de busca de telemetria do Arkhe
                // Em um cenário real, isso viria de /api/v1/fab-telemetry
                const response = await fetch('/api/visualization-state');
                if (response.ok) {
                    const data = await response.json();
                    // Mapeamento mock de estado para parâmetros de fábrica
                    if (data.nodes && data.nodes.length > 0) {
                        const alertCount = data.nodes.filter((n: { securityState: number }) => n.securityState > 0).length;
                        setTelemetry(prev => ({
                            ...prev,
                            waferDefectRate: 0.05 + alertCount * 0.1,
                            alignmentError: alertCount > 2 ? 0.01 : 0.0
                        }));
                    }
                }
            } catch {
                // Silently ignore telemetry fetch errors in mock view
            }
        };
        const interval = setInterval(fetchTelemetry, 3000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) {return;}
        const gl = canvas.getContext('webgl2');
        if (!gl) {return;}

        const createShader = (gl: WebGL2RenderingContext, type: number, source: string) => {
            const shader = gl.createShader(type)!;
            gl.shaderSource(shader, source);
            gl.compileShader(shader);
            if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
                console.error(gl.getShaderInfoLog(shader));
            }
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
        const defectLoc = gl.getUniformLocation(program, 'uWaferDefectRate');
        const oxideLoc = gl.getUniformLocation(program, 'uOxideThickness');
        const dopingLoc = gl.getUniformLocation(program, 'uDopingConcentration');
        const alignLoc = gl.getUniformLocation(program, 'uAlignmentError');
        const etchLoc = gl.getUniformLocation(program, 'uEtchDepth');

        const render = (time: number) => {
            if (!canvasRef.current) {return;}
            gl.viewport(0, 0, canvas.width, canvas.height);
            gl.uniform2f(resLoc, canvas.width, canvas.height);
            gl.uniform1f(timeLoc, time * 0.001);

            gl.uniform1f(defectLoc, telemetry.waferDefectRate);
            gl.uniform1f(oxideLoc, telemetry.oxideThickness);
            gl.uniform1f(dopingLoc, telemetry.dopingConcentration);
            gl.uniform1f(alignLoc, telemetry.alignmentError);
            gl.uniform1f(etchLoc, telemetry.etchDepth);

            gl.drawArrays(gl.TRIANGLES, 0, 6);
            requestRef.current = requestAnimationFrame(render);
        };

        requestRef.current = requestAnimationFrame(render);
        return () => cancelAnimationFrame(requestRef.current);
    }, [telemetry]);

    return (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/95 backdrop-blur-xl p-4">
            <div className="w-full max-w-6xl bg-[#0d0e12] border border-amber-500/30 rounded-3xl shadow-[0_0_80px_rgba(245,158,11,0.15)] overflow-hidden flex flex-col h-[85vh]">
                <div className="flex items-center justify-between p-6 border-b border-amber-500/20 bg-amber-500/5">
                    <div className="flex items-center gap-5">
                        <div className="p-3 bg-amber-500/10 rounded-2xl border border-amber-500/30">
                            <Cpu className="w-8 h-8 text-amber-500" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-amber-500 tracking-[0.25em] uppercase font-mono">Observatório de Silício</h2>
                            <div className="text-[10px] font-mono text-amber-500/60 flex items-center gap-2 mt-1">
                                <Activity className="w-4 h-4 text-amber-400" />
                                Auditoria Visual de Manufatura — ANEXO AS
                            </div>
                        </div>
                    </div>
                    <button onClick={onClose} className="group flex items-center gap-3 px-5 py-2.5 border border-white/10 rounded-xl text-neutral-500 hover:text-white hover:border-white transition-all bg-white/5">
                        <span className="text-[10px] font-mono uppercase tracking-[0.2em]">FECHAR MÓDULO</span>
                        <X className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                    </button>
                </div>

                <div className="flex-1 relative flex flex-col lg:flex-row overflow-hidden">
                    <div className="flex-1 relative bg-[#050507]">
                        <canvas
                            ref={canvasRef}
                            width={1280}
                            height={720}
                            className="w-full h-full object-contain"
                        />

                        <div className="absolute bottom-8 left-8 flex flex-col gap-4">
                            <div className="flex items-center gap-4 px-5 py-3 bg-black/80 border border-amber-500/20 rounded-xl backdrop-blur-md">
                                <Shield className="w-4 h-4 text-amber-500" />
                                <span className="text-[10px] font-mono text-amber-200 uppercase tracking-widest font-bold">Protocolo de Integridade: ATIVO</span>
                            </div>
                        </div>

                        <div className="absolute top-8 right-8">
                            <div className="grid grid-cols-1 gap-2">
                                {['LITOGRAFIA', 'ETCHING', 'DOPAGEM', 'METALIZAÇÃO'].map((step, i) => (
                                    <div key={i} className="flex items-center gap-3 px-4 py-2 bg-black/60 border border-white/5 rounded-lg text-[9px] font-mono text-neutral-400">
                                        <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                                        {step} STATUS: OK
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="w-full lg:w-80 bg-[#0a0b0e] border-l border-white/5 p-8 flex flex-col gap-8 overflow-y-auto">
                        <div className="space-y-6">
                            <div className="flex items-center gap-3 text-amber-500/80">
                                <Settings2 className="w-5 h-5" />
                                <h4 className="font-mono text-xs uppercase font-bold tracking-widest">Controles de Telemetria</h4>
                            </div>

                            <div className="space-y-6">
                                <div className="space-y-3">
                                    <div className="flex justify-between text-[10px] font-mono text-neutral-500 uppercase">
                                        <span>Taxa de Defeitos</span>
                                        <span className={telemetry.waferDefectRate > 0.1 ? 'text-rose-400' : 'text-amber-400'}>
                                            {(telemetry.waferDefectRate * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <input
                                        type="range" min="0" max="0.5" step="0.01"
                                        value={telemetry.waferDefectRate}
                                        onChange={(e) => setTelemetry(t => ({...t, waferDefectRate: parseFloat(e.target.value)}))}
                                        className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-amber-500"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <div className="flex justify-between text-[10px] font-mono text-neutral-500 uppercase">
                                        <span>Espessura do Óxido</span>
                                        <span className="text-amber-400">{telemetry.oxideThickness.toFixed(2)}nm</span>
                                    </div>
                                    <input
                                        type="range" min="0.1" max="1.0" step="0.05"
                                        value={telemetry.oxideThickness}
                                        onChange={(e) => setTelemetry(t => ({...t, oxideThickness: parseFloat(e.target.value)}))}
                                        className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-amber-500"
                                    />
                                </div>

                                <div className="space-y-3">
                                    <div className="flex justify-between text-[10px] font-mono text-neutral-500 uppercase">
                                        <span>Erro de Alinhamento</span>
                                        <span className={telemetry.alignmentError > 0.005 ? 'text-rose-400' : 'text-amber-400'}>
                                            {(telemetry.alignmentError * 1000).toFixed(1)}nm
                                        </span>
                                    </div>
                                    <input
                                        type="range" min="0" max="0.05" step="0.001"
                                        value={telemetry.alignmentError}
                                        onChange={(e) => setTelemetry(t => ({...t, alignmentError: parseFloat(e.target.value)}))}
                                        className="w-full h-1.5 bg-white/5 rounded-lg appearance-none cursor-pointer accent-amber-500"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="mt-auto space-y-4">
                            <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded-2xl space-y-3">
                                <div className="flex items-center gap-2 text-amber-500">
                                    <Info className="w-4 h-4" />
                                    <span className="font-mono text-[10px] uppercase font-bold">Ontologia Visual</span>
                                </div>
                                <p className="text-[9px] font-mono text-neutral-500 leading-relaxed">
                                    O shader traduz o processo de dopagem e litografia em campos de distância assinados (SDF), permitindo a auditoria visual da topologia do chip em tempo real.
                                </p>
                            </div>

                            <button className="w-full py-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-500 font-mono text-[10px] uppercase tracking-[0.2em] hover:bg-amber-500/20 transition-all flex items-center justify-center gap-2">
                                <Search className="w-4 h-4" />
                                Iniciar Scan de Defeitos
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
