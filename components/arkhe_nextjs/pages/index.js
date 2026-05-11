import { useEffect, useState, useRef } from 'react';
import Head from 'next/head';
import * as THREE from 'three';
import * as tf from '@tensorflow/tfjs';

export default function Home() {
  const [omega, setOmega] = useState(0.94);
  const [prediction, setPrediction] = useState(null);
  const modelRef = useRef(null);
  const mountRef = useRef(null);

  // 1. Initialize Three.js 3D Visualization
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

    const light = new THREE.PointLight(0xffffff, 1, 100);
    light.position.set(10, 10, 10);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x404040));

    camera.position.z = 10;

    const animate = () => {
      requestAnimationFrame(animate);
      core.rotation.x += 0.01;
      core.rotation.y += 0.01;
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      mountRef.current?.removeChild(renderer.domElement);
    };
  }, []);

  // 2. Initialize TensorFlow.js Predictive Ethics Model
  useEffect(() => {
    const initModel = async () => {
      const model = tf.sequential();
      model.add(tf.layers.dense({ units: 8, inputShape: [1], activation: 'relu' }));
      model.add(tf.layers.dense({ units: 1 }));
      model.compile({ optimizer: 'sgd', loss: 'meanSquaredError' });
      modelRef.current = model;
      console.log("🧠 TF.js Ethics Model Initialized");
    };
    initModel();
  }, []);

  // 3. Fetch Telemetry and Run Prediction
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('/api/telemetry');
        const data = await res.json();
        setOmega(data.omega);

        if (modelRef.current) {
          const xs = tf.tensor2d([data.omega], [1, 1]);
          const ys = tf.tensor2d([data.omega * 0.98], [1, 1]);
          await modelRef.current.fit(xs, ys, { epochs: 1 });

          const pred = modelRef.current.predict(xs);
          setPrediction(pred.dataSync()[0]);
        }
      } catch (e) { console.error(e); }
    };
    const interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '40px', backgroundColor: '#000', color: '#0ff', minHeight: '100vh', fontFamily: 'monospace' }}>
      <Head>
        <title>Arkhe OS | Frontend Cósmico v18</title>
        <meta name="description" content="Arkhe OS Nexus Dashboard featuring Ethical Predictive TF.js integration and Real-Time 3D WebGL visualizations." />
        <meta name="keywords" content="Arkhe OS, Quantum, OS, TF.js, 3D, WebGL, AI, Predictive Ethics" />
        <meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1" />
        <meta name="OAI-SearchBot" content="index, follow" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              "name": "Arkhe OS",
              "operatingSystem": "Any",
              "applicationCategory": "SystemSoftware",
              "description": "Arkhe OS Nexus Dashboard featuring Ethical Predictive TF.js integration and Real-Time 3D WebGL visualizations.",
              "offers": {
                "@type": "Offer",
                "price": "0.00",
                "priceCurrency": "USD"
              }
            })
          }}
        />
      </Head>
      <h1>🌌 Arkhe OS | Frontend Cósmico v18</h1>

      <div style={{ display: 'flex', gap: '40px', alignItems: 'center' }}>
        <div style={{ border: '1px solid #0ff', padding: '20px', borderRadius: '10px', flex: 1 }}>
          <p>Ω Coherence (from C++ Kernel): <strong>{omega.toFixed(4)}</strong></p>
          <p>Ethical Prediction (TF.js): <strong>{prediction ? prediction.toFixed(4) : 'Predicting...'}</strong></p>
          <p style={{ marginTop: '20px', opacity: 0.6 }}>Executing predictive ethics on client-side neural mesh.</p>
        </div>

        <div ref={mountRef} style={{ border: '1px solid #0ff', borderRadius: '10px', overflow: 'hidden' }} />
      </div>

      <div style={{ marginTop: '40px' }}>
        <h2>System Status: <span style={{ color: '#f0f' }}>OPERATIONAL_V18</span></h2>
      </div>
    </div>
  );
}
