import React, { useState } from 'react';
import { View, Text, TouchableOpacity, ScrollView, TextInput, StyleSheet } from 'react-native';
import { useStore } from '../store/attractorStore';

const DOMAIN_PROFILES = [
  { id: 'default', label: '🌐 Padrão', alpha: 1.5, beta: 0.4, gamma: 0.3, T: 0.8 },
  { id: 'creative', label: '🎨 Criativo', alpha: 2.0, beta: 0.6, gamma: 0.4, T: 0.9 },
  { id: 'technical', label: '⚙️ Técnico', alpha: 1.0, beta: 0.2, gamma: 0.6, T: 0.6 },
  { id: 'educational', label: '📚 Educacional', alpha: 1.5, beta: 0.5, gamma: 0.5, T: 0.8 },
  { id: 'scientific', label: '🔬 Científico', alpha: 1.8, beta: 0.3, gamma: 0.7, T: 0.7 },
];

export const DomainSelector: React.FC = () => {
  const { activeProfile, setProfile, syncWithEngine } = useStore();
  const [alpha, setAlpha] = useState(activeProfile.alpha);
  const [beta, setBeta] = useState(activeProfile.beta);
  const [gamma, setGamma] = useState(activeProfile.gamma);
  const [temp, setTemp] = useState(activeProfile.T);

  const selectDomain = async (profile: typeof DOMAIN_PROFILES[0]) => {
    setProfile(profile);
    setAlpha(profile.alpha);
    setBeta(profile.beta);
    setGamma(profile.gamma);
    setTemp(profile.T);

    // Injetar parâmetros no motor de geração via API local
    await fetch('http://localhost:8051/api/attractor/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    await syncWithEngine();
  };

  const handleSliderChange = async () => {
    const customProfile = { ...activeProfile, alpha, beta, gamma, T: temp, id: 'custom' };
    setProfile(customProfile);
    await fetch('http://localhost:8051/api/attractor/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(customProfile),
    });
    await syncWithEngine();
  }

  return (
    <View style={{ flex: 1 }}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ padding: 12, flexGrow: 0 }}>
        {DOMAIN_PROFILES.map((p) => (
          <TouchableOpacity
            key={p.id}
            onPress={() => selectDomain(p)}
            style={{
              padding: 12, marginRight: 10, borderRadius: 12,
              backgroundColor: activeProfile.id === p.id ? '#3498db' : '#ecf0f1',
              borderWidth: 1, borderColor: activeProfile.id === p.id ? '#2980b9' : '#bdc3c7',
            }}
          >
            <Text style={{ color: activeProfile.id === p.id ? '#fff' : '#2c3e50', fontWeight: '600' }}>
              {p.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <View style={{ padding: 12 }}>
         <Text>Alpha (α): {alpha}</Text>
         <TextInput style={styles.input} keyboardType="numeric" value={String(alpha)} onChangeText={v => setAlpha(Number(v))} onBlur={handleSliderChange} />

         <Text>Beta (β): {beta}</Text>
         <TextInput style={styles.input} keyboardType="numeric" value={String(beta)} onChangeText={v => setBeta(Number(v))} onBlur={handleSliderChange} />

         <Text>Gamma (γ): {gamma}</Text>
         <TextInput style={styles.input} keyboardType="numeric" value={String(gamma)} onChangeText={v => setGamma(Number(v))} onBlur={handleSliderChange} />

         <Text>Temperature (T): {temp}</Text>
         <TextInput style={styles.input} keyboardType="numeric" value={String(temp)} onChangeText={v => setTemp(Number(v))} onBlur={handleSliderChange} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  input: {
    height: 40,
    margin: 12,
    borderWidth: 1,
    padding: 10,
  },
});
