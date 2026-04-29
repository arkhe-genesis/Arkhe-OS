'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { NMMEngine } from '@/lib/animation/src/engine/NMMEngine';

export const NeuralAnimationPanel: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [engine, setEngine] = useState<NMMEngine | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    let animationFrameId: number;
    let currentEngine: NMMEngine;

    const init = async () => {
      try {
        const { default: WebGPURenderer } = await import('three/examples/jsm/renderers/webgpu/WebGPURenderer.js' as any);

        const renderer = new WebGPURenderer({
          canvas: canvasRef.current!,
          antialias: true,
        });

        renderer.setSize(containerRef.current!.clientWidth, containerRef.current!.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);

        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x020305);

        const camera = new THREE.PerspectiveCamera(
          45,
          containerRef.current!.clientWidth / containerRef.current!.clientHeight,
          0.1,
          100
        );
        camera.position.set(3, 2, 5);
        camera.lookAt(0, 1, 0);

        const grid = new THREE.GridHelper(20, 20, 0x333333, 0x111111);
        scene.add(grid);

        const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 3);
        hemiLight.position.set(0, 20, 0);
        scene.add(hemiLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 3);
        dirLight.position.set(3, 10, 10);
        scene.add(dirLight);

        currentEngine = await NMMEngine.load({
          renderer: renderer as any,
          bundleBaseUrl: '/lib/animation/',
          characterGlbUrl: '/lib/animation/assets/geno.glb',
          maxAgents: 1,
          bundleKind: 'biped'
        });

        scene.add(currentEngine.mesh);

        currentEngine.createAgent({
          position: [0, 0, 0] as any,
          facing: [0, 0, 0, 1] as any,
          style: 'idle'
        });

        setEngine(currentEngine);
        setLoading(false);

        const clock = new THREE.Clock();

        const animate = () => {
          animationFrameId = requestAnimationFrame(animate);
          const dt = clock.getDelta();

          currentEngine.update(dt);
          renderer.render(scene, camera);
        };

        animate();
      } catch (error) {
        console.error('Failed to initialize Neural Animation:', error);
        setLoading(false);
      }
    };

    init();

    return () => {
      cancelAnimationFrame(animationFrameId);
      if (currentEngine) currentEngine.dispose();
    };
  }, []);

  return (
    <div className="bg-black/40 border border-white/5 rounded-3xl p-6 space-y-4 overflow-hidden relative" ref={containerRef} style={{ height: '400px' }}>
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-widest">Neural Motion Matching</h3>
          <p className="text-[10px] text-slate-500">Real-time WebGPU Inference</p>
        </div>
        <div className="flex gap-2">
          {engine?.styles.map((style) => (
             <button key={style} className="px-2 py-1 bg-white/5 hover:bg-white/10 rounded text-[8px] uppercase font-bold text-slate-400">
               {style}
             </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60 z-10">
           <div className="flex flex-col items-center gap-2">
              <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
              <p className="text-[10px] font-mono text-cyan-500 uppercase tracking-widest">Loading Neural Weights...</p>
           </div>
        </div>
      )}

      <canvas ref={canvasRef} className="w-full h-full rounded-2xl" />

      <div className="absolute bottom-10 left-10 pointer-events-none">
         <div className="bg-black/60 backdrop-blur-md p-3 rounded-xl border border-white/5">
            <p className="text-[8px] text-slate-500 mb-1 font-mono uppercase">Inference Latency</p>
            <p className="text-xs font-bold text-emerald-400 font-mono">
              {engine ? `${engine.lastComputeMs.toFixed(2)}ms` : '0.00ms'}
            </p>
         </div>
      </div>
    </div>
  );
};
