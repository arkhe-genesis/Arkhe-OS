// ============================================================================
// ARKHE IMMERSIVE — Interface AR/VR para visualização de estados quânticos
// React Native + Three.js + WebXR + Plotly 3D
// ============================================================================
import React, {useRef, useEffect, useState} from 'react';
import {View, Text, StyleSheet, Button, Slider} from 'react-native';
import {Canvas, useFrame, useThree} from '@react-three/fiber';
import {XR, useXR} from '@react-three/xr';
import {Sphere, Box, Line} from '@react-three/drei';
import * as THREE from 'three';
// import {PhiCFieldVisualizer, QuantumStateMesh, EpigeneticHeatmap} from './components';

const ARKHE_IMMERSIVE_THEME = {
  background: '#000814',
  quantumState: '#00d4aa',
  epigeneticMark: '#ff6b6b',
  coherenceField: '#4ecdc4',
  text: '#e2e8f0',
};

export default function ArkheImmersive() {
  const {isPresenting, session} = useXR();
  const [viewMode, setViewMode] = useState<'quantum' | 'epigenetic' | 'temporal'>('quantum');
  const [phiCSlider, setPhiCSlider] = useState(0.99);
  const [selectedState, setSelectedState] = useState<string | null>(null);

  // Carregar dados quânticos iniciais
  const [quantumData, setQuantumData] = useState<any>(null);

  useEffect(() => {
    loadQuantumData();
  }, []);

  const loadQuantumData = async () => {
    // Fetch de dados quânticos da API Arkhe
    try {
        const response = await fetch('https://api.arkhe.org/v1/quantum/states');
        const data = await response.json();
        setQuantumData(data);
    } catch (e) {
        console.warn("Failed to load quantum data from API", e);
    }
  };

  const handleStateSelect = (stateId: string) => {
    setSelectedState(stateId);
    // Mostrar detalhes do estado em overlay
  };

  return (
    <View style={styles.container}>
      {/* Canvas 3D/WebXR */}
      <Canvas
        camera={{position: [0, 0, 5], fov: 75}}
        style={styles.canvas}
      >
        <XR>
          {/* Ambiente imersivo */}
          <color attach="background" args={[ARKHE_IMMERSIVE_THEME.background]} />
          <ambientLight intensity={0.3} />
          <pointLight position={[10, 10, 10]} intensity={0.8} />

          {/* Visualização baseada no modo selecionado */}
          {viewMode === 'quantum' && (
            <QuantumStateMesh
              data={quantumData}
              onSelect={handleStateSelect}
              coherence={phiCSlider}
            />
          )}

          {viewMode === 'epigenetic' && (
             <group></group> // Placeholder
            // <EpigeneticHeatmap
            //   region="RADIX-2_promoter"
            //   cellType="stem"
            //   generation={0}
            // />
          )}

          {viewMode === 'temporal' && (
              <group></group> // Placeholder
            // <PhiCFieldVisualizer
            //   trajectory={quantumData?.phi_c_history || []}
            //   currentTime={Date.now()}
            // />
          )}

          {/* Grid de referência */}
          <gridHelper args={[20, 20, 0x444466, 0x222244]} />
        </XR>
      </Canvas>

      {/* UI Overlay */}
      <View style={styles.overlay}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>🧬 ARKHE IMMERSIVE</Text>
          <Text style={styles.subtitle}>
            {isPresenting ? '🥽 VR Mode' : '📱 AR Mode'}
          </Text>
        </View>

        {/* Controles de visualização */}
        <View style={styles.controls}>
          <Button
            title="Quantum States"
            onPress={() => setViewMode('quantum')}
            color={viewMode === 'quantum' ? ARKHE_IMMERSIVE_THEME.quantumState : '#666'}
          />
          <Button
            title="Epigenetic Map"
            onPress={() => setViewMode('epigenetic')}
            color={viewMode === 'epigenetic' ? ARKHE_IMMERSIVE_THEME.epigeneticMark : '#666'}
          />
          <Button
            title="Temporal Φ_C"
            onPress={() => setViewMode('temporal')}
            color={viewMode === 'temporal' ? ARKHE_IMMERSIVE_THEME.coherenceField : '#666'}
          />
        </View>

        {/* Slider de coerência Φ_C */}
        <View style={styles.sliderContainer}>
          <Text style={styles.sliderLabel}>Φ_C Coherence: {phiCSlider.toFixed(4)}</Text>
          <Slider
            value={phiCSlider}
            onValueChange={setPhiCSlider}
            minimumValue={0.90}
            maximumValue={1.0}
            step={0.0001}
            minimumTrackTintColor={ARKHE_IMMERSIVE_THEME.coherenceField}
            maximumTrackTintColor="#444"
          />
        </View>

        {/* Detalhes do estado selecionado */}
        {selectedState && quantumData?.states?.[selectedState] && (
          <View style={styles.detailsPanel}>
            <Text style={styles.detailsTitle}>Detalhes do Estado</Text>
            <Text>ID: {selectedState}</Text>
            <Text>Fidelidade: {quantumData.states[selectedState].fidelity?.toFixed(4)}</Text>
            <Text>Dimensão: {quantumData.states[selectedState].dimension}</Text>
            <Button title="Fechar" onPress={() => setSelectedState(null)} />
          </View>
        )}

        {/* Footer com métricas */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            🌀 Φ_C Global: {quantumData?.global_phi_c?.toFixed(4) || '—'}
            {' • '}
            🔗 Nós Ativos: {quantumData?.active_nodes || '—'}
          </Text>
        </View>
      </View>
    </View>
  );
}

// ============================================================================
// Componente: QuantumStateMesh — Visualização 3D de estados quânticos
// ============================================================================
function QuantumStateMesh({data, onSelect, coherence}: any) {
  const meshRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    // Rotação suave do mesh
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.1;
    }
  });

  if (!data?.states) return null;

  return (
    <group ref={meshRef}>
      {Object.entries(data.states).map(([id, state]: [string, any]) => (
        <Sphere
          key={id}
          args={[0.3]}
          position={state.position || [0, 0, 0]}
          onClick={() => onSelect(id)}
        >
          <meshStandardMaterial
            color={ARKHE_IMMERSIVE_THEME.quantumState}
            opacity={coherence}
            transparent
            metalness={0.8}
            roughness={0.2}
          />
        </Sphere>
      ))}

      {/* Linhas de emaranhamento entre estados */}
      {data.entanglements?.map((ent: any, i: number) => (
        <Line
          key={i}
          points={[ent.state1_pos, ent.state2_pos]}
          color={ARKHE_IMMERSIVE_THEME.coherenceField}
          lineWidth={1}
          transparent
          opacity={ent.strength * coherence}
        />
      ))}
    </group>
  );
}

// Estilos
const styles = StyleSheet.create({
  container: {flex: 1, backgroundColor: '#000'},
  canvas: {flex: 1},
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: 'none',
  },
  header: {
    padding: 16,
    backgroundColor: 'rgba(0, 8, 20, 0.8)',
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  title: {fontSize: 20, fontWeight: 'bold', color: ARKHE_IMMERSIVE_THEME.text},
  subtitle: {fontSize: 14, color: '#94a3b8'},
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 12,
    backgroundColor: 'rgba(0, 8, 20, 0.9)',
    pointerEvents: 'auto',
  },
  sliderContainer: {
    padding: 16,
    backgroundColor: 'rgba(0, 8, 20, 0.9)',
    pointerEvents: 'auto',
  },
  sliderLabel: {color: ARKHE_IMMERSIVE_THEME.text, marginBottom: 8},
  detailsPanel: {
    position: 'absolute',
    bottom: 100,
    left: 16,
    right: 16,
    padding: 16,
    backgroundColor: 'rgba(22, 42, 74, 0.95)',
    borderRadius: 12,
    pointerEvents: 'auto',
  },
  detailsTitle: {fontSize: 16, fontWeight: '600', marginBottom: 8},
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 12,
    backgroundColor: 'rgba(0, 8, 20, 0.9)',
    alignItems: 'center',
  },
  footerText: {color: '#94a3b8', fontSize: 12},
});
