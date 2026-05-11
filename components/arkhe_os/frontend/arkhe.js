// arkhe_os/frontend/arkhe.js — Arkhe OS Frontend (React/Next.js)
import { useEffect, useState, useRef } from 'react';
import * as THREE from 'three';
import { io } from 'socket.io-client';
import * as tf from '@tensorflow/tfjs';

export default function ArkheDashboard() {
  const [omega, setOmega] = useState(0.94);
  const [kEth, setKEth] = useState(0.92);
  const mountRef = useRef(null);

  useEffect(() => {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(400, 400);
    mountRef.current?.appendChild(renderer.domElement);

    const geometry = new THREE.TorusKnotGeometry(2, 0.6, 128, 32);
    const material = new THREE.MeshPhongMaterial({ color: 0x00ffff, emissive: 0x002244 });
    const core = new THREE.Mesh(geometry, material);
    scene.add(core);

    const animate = () => {
      requestAnimationFrame(animate);
      core.rotation.x += 0.01;
      core.rotation.y += 0.01;
      renderer.render(scene, camera);
    };
    animate();
  }, []);

  return (
    <div className="arkhe-dashboard">
      <h1>🌌 Arkhe OS Dashboard (v17)</h1>
      <div className="metrics">
        <div>Ω: {omega.toFixed(4)}</div>
        <div>K_eth: {kEth.toFixed(4)}</div>
      </div>
      <div className="coherence-field-3d" ref={mountRef} />
    </div>
  );
}
