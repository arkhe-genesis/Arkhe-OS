'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

interface ArkheCore3DProps {
  omega: number;
  kEth: number;
}

export default function ArkheCore3D({ omega, kEth }: ArkheCore3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

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
    controls.autoRotateSpeed = 0.3;

    const shaderMaterial = new THREE.ShaderMaterial({
      uniforms: {
        uTime: { value: 0 },
        uOmega: { value: omega },
        uKEth: { value: kEth },
      },
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vPosition;
        varying vec3 vNormal;
        void main() {
          vUv = uv;
          vPosition = position;
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float uTime;
        uniform float uOmega;
        uniform float uKEth;
        varying vec2 vUv;
        varying vec3 vPosition;
        varying vec3 vNormal;
        void main() {
          vec3 colorBase = vec3(0.0, 0.8, 1.0);
          vec3 colorEthical = vec3(1.0, 0.4, 1.0);
          vec3 color = mix(colorBase, colorEthical, uKEth);
          float fresnel = pow(1.0 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
          float pulse = sin(uTime * 3.0 + vPosition.y * 2.0) * 0.5 + 0.5;
          float alpha = 0.6 + fresnel * 0.4 + pulse * 0.1 * uOmega;
          color += vec3(pulse * 0.2);
          gl_FragColor = vec4(color, alpha);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide,
    });

    const geometry = new THREE.TorusKnotGeometry(2, 0.6, 128, 32);
    const core = new THREE.Mesh(geometry, shaderMaterial);
    scene.add(core);

    const clock = new THREE.Clock();
    const animate = () => {
      requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      shaderMaterial.uniforms.uTime.value = elapsed;
      shaderMaterial.uniforms.uOmega.value = omega;
      shaderMaterial.uniforms.uKEth.value = kEth;

      core.rotation.x += 0.002;
      core.rotation.y += 0.003;
      core.scale.setScalar(0.8 + omega * 0.4);

      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!containerRef.current) return;
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
  }, [omega, kEth]);

  return <div ref={containerRef} className="w-full h-full min-h-[400px] rounded-xl" />;
}
