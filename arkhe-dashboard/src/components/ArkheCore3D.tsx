
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

interface ArkheCore3DProps {
  omega: number;
  kEth: number;
  scaffoldMode?: boolean;
  fibonacciVision?: boolean;
}

export default function ArkheCore3D({ omega, kEth, scaffoldMode = false, fibonacciVision = false }: ArkheCore3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) {return;}

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      60,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(5, 3, 8);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    containerRef.current.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.autoRotate = true;
    controls.autoRotateSpeed = scaffoldMode ? 0.8 : 0.3;

    // Enhanced Shader for Scaffold & Fibonacci Vision
    const shaderMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uOmega: { value: omega },
        uKEth: { value: kEth },
        uScaffoldMode: { value: scaffoldMode ? 1.0 : 0.0 },
        uFibonacciVision: { value: fibonacciVision ? 1.0 : 0.0 },
      },
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vPosition;
        varying vec3 vNormal;
        uniform float uScaffoldMode;
        uniform float uFibonacciVision;
        uniform float uTime;

        void main() {
          vUv = uv;
          vNormal = normalize(normalMatrix * normal);

          vec3 pos = position;
          if (uScaffoldMode > 0.5) {
             // Simular protofilamentos: deformação longitudinal (Euler Curvature)
             float wave = sin(pos.y * 10.0 + uTime * 5.0) * 0.05;
             pos.x += wave * vNormal.x;
             pos.z += wave * vNormal.z;
          }

          if (uFibonacciVision > 0.5) {
             // Vibração de Fibonacci
             pos += vNormal * sin(uTime * 13.0) * 0.02 * uScaffoldMode;
          }

          vPosition = pos;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform float uOmega;
        uniform float uKEth;
        uniform float uScaffoldMode;
        uniform float uFibonacciVision;
        varying vec2 vUv;
        varying vec3 vPosition;
        varying vec3 vNormal;

        void main() {
          vec3 colorBase = vec3(0.0, 0.8, 1.0);
          vec3 colorEthical = vec3(1.0, 0.4, 1.0);
          vec3 colorScaffold = vec3(0.5, 0.0, 1.0); // Violeta UV
          vec3 colorFibonacci = vec3(0.0, 1.0, 0.6); // Verde Áureo

          vec3 color = mix(colorBase, colorEthical, uKEth);

          if (uScaffoldMode > 0.5) {
            float stripe = step(0.9, sin(vUv.x * 50.0 + uTime * 10.0));
            color = mix(colorScaffold, vec3(1.0, 1.0, 1.0), stripe);
          }

          if (uFibonacciVision > 0.5) {
            // Picos de Fibonacci visualizados como anéis de luz
            float ring = step(0.95, sin(vPosition.y * 5.0 - uTime * 3.0));
            color = mix(color, colorFibonacci, ring);
          }

          float fresnel = pow(1.0 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
          float pulse = sin(uTime * (uScaffoldMode > 0.5 ? 10.0 : 3.0) + vPosition.y * 2.0) * 0.5 + 0.5;
          float alpha = (uScaffoldMode > 0.5 ? 0.4 : 0.6) + fresnel * 0.4 + pulse * 0.1 * uOmega;

          color += vec3(pulse * 0.2);
          gl_FragColor = vec4(color, alpha);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide,
    });

    let geometry: THREE.BufferGeometry;

    if (scaffoldMode) {
      // Microtubule Cylinder with 13 protofilaments
      geometry = new THREE.CylinderGeometry(1.5, 1.5, 6, 13, 64, true);
    } else {
      geometry = new THREE.TorusKnotGeometry(2, 0.6, 128, 32);
    }

    const core = new THREE.Mesh(geometry, shaderMaterial);
    scene.add(core);

    const clock = new THREE.Clock();
    const animate = () => {
      requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      shaderMaterial.uniforms.uTime.value = elapsed;
      shaderMaterial.uniforms.uOmega.value = omega;
      shaderMaterial.uniforms.uKEth.value = kEth;
      shaderMaterial.uniforms.uScaffoldMode.value = scaffoldMode ? 1.0 : 0.0;
      shaderMaterial.uniforms.uFibonacciVision.value = fibonacciVision ? 1.0 : 0.0;

      core.rotation.x += 0.002;
      core.rotation.y += 0.003;
      core.scale.setScalar(0.8 + omega * 0.4);

      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!containerRef.current) {return;}
      camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      containerRef.current?.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, [omega, kEth, scaffoldMode, fibonacciVision]);

  return <div ref={containerRef} className="w-full h-full min-h-[400px] rounded-xl" />;
}
