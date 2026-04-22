
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Tv, Wind, Droplets, Zap, Activity, Cpu, Play, Pause, Database } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState, useEffect } from 'react';

interface ArkheTVPanelProps {
  onClose: () => void;
}

export default function ArkheTVPanel({ onClose }: ArkheTVPanelProps) {
  const [activeModule, setActiveModule] = useState<'ginga' | 'guarana' | 'pocai' | 'pi2'>('ginga');
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackTime, setPlaybackTime] = useState(0);
  const [sensoryEvents, setSensoryEvents] = useState<Array<{type: string, intensity: number, target: string, time: number}>>([]);

  // Simulation of the amazonia.ncl playback
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isPlaying) {
      interval = setInterval(() => {
        setPlaybackTime(prev => {
          const newTime = prev + 1;
          
          // Trigger sensory events based on NCL script
          if (newTime === 10) {
            setSensoryEvents(curr => [...curr, { type: 'wind', intensity: 0.7, target: 'fan_living_room', time: newTime }]);
          } else if (newTime === 30) {
            setSensoryEvents(curr => [...curr, { type: 'scent', intensity: 0.5, target: 'diffuser_living_room', time: newTime }]);
          } else if (newTime >= 60) {
            setIsPlaying(false);
            return 0; // Reset at end
          }
          
          return newTime;
        });
      }, 1000); // 1 second = 1 second in simulation
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const togglePlayback = () => {
    if (!isPlaying && playbackTime >= 60) {
      setPlaybackTime(0);
      setSensoryEvents([]);
    }
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-fuchsia-500/30 rounded-xl w-full max-w-6xl overflow-hidden shadow-[0_0_40px_rgba(217,70,239,0.15)] flex flex-col h-[85vh]"
      >
        {/* Header */}
        <div className="p-4 border-b border-fuchsia-500/20 flex justify-between items-center bg-fuchsia-500/5 shrink-0">
          <div className="flex items-center gap-3">
            <Tv className="w-5 h-5 text-fuchsia-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-fuchsia-400 font-bold">
              ArkheTV — TV 3.0 Ontológica
            </h2>
            <span className="px-2 py-0.5 bg-fuchsia-500/20 text-fuchsia-400 text-[10px] font-mono rounded border border-fuchsia-500/30">
              DTV+ EXTENSION
            </span>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Navigation */}
          <div className="w-56 border-r border-fuchsia-500/20 bg-[#0d0e12] p-4 flex flex-col gap-2 shrink-0 overflow-y-auto custom-scrollbar">
            <div className="text-[10px] font-mono text-fuchsia-400/50 uppercase tracking-widest mb-2">Architecture Modules</div>
            
            <button
              onClick={() => setActiveModule('ginga')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors text-left ${activeModule === 'ginga' ? 'bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <Cpu className="w-4 h-4 shrink-0" /> 
              <span>M1: Ginga-Core<br/><span className="text-[9px] opacity-70">Middleware Estendido</span></span>
            </button>
            
            <button
              onClick={() => setActiveModule('guarana')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors text-left ${activeModule === 'guarana' ? 'bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <Activity className="w-4 h-4 shrink-0" /> 
              <span>M3: Guaraná-Tzinor<br/><span className="text-[9px] opacity-70">Protocolo de Rede</span></span>
            </button>
            
            <button
              onClick={() => setActiveModule('pocai')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors text-left ${activeModule === 'pocai' ? 'bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <Database className="w-4 h-4 shrink-0" /> 
              <span>M4: PoC-AI<br/><span className="text-[9px] opacity-70">Recomendação Retrocausal</span></span>
            </button>
            
            <button
              onClick={() => setActiveModule('pi2')}
              className={`flex items-center gap-2 px-3 py-2 rounded text-xs font-mono transition-colors text-left ${activeModule === 'pi2' ? 'bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
            >
              <Zap className="w-4 h-4 shrink-0" /> 
              <span>M5: π² Signer<br/><span className="text-[9px] opacity-70">Verificação Criptográfica</span></span>
            </button>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 flex flex-col bg-[#0a0a0c] overflow-hidden">
            
            {/* Top: Simulation Area */}
            <div className="h-64 border-b border-fuchsia-500/20 bg-black relative flex flex-col shrink-0">
              <div className="absolute top-2 left-2 px-2 py-1 bg-black/60 border border-fuchsia-500/30 rounded text-[10px] font-mono text-fuchsia-400 z-10">
                NCL-ONTO SIMULATION: amazonia.ncl
              </div>
              
              {/* Video Area Simulation */}
              <div className="flex-1 relative overflow-hidden flex items-center justify-center">
                {/* Background visual based on time */}
                <div className={`absolute inset-0 transition-opacity duration-1000 ${playbackTime >= 10 && playbackTime < 30 ? 'bg-blue-900/20' : playbackTime >= 30 ? 'bg-green-900/20' : 'bg-[#0a0a0c]'}`}></div>
                
                {/* Scanlines */}
                <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%] opacity-30 z-0"></div>
                
                <div className="z-10 text-center font-mono">
                  <div className="text-4xl font-bold text-white/80 mb-2">
                    {playbackTime < 10 ? 'INTRO' : playbackTime < 30 ? 'RIVER' : 'FOREST'}
                  </div>
                  <div className="text-fuchsia-400 text-xl">
                    00:00:{playbackTime.toString().padStart(2, '0')}
                  </div>
                </div>

                {/* Sensory Event Indicators */}
                <AnimatePresence>
                  {sensoryEvents.map((event, _i) => (
                    <motion.div 
                      key={`${event.type}-${event.time}`}
                      initial={{ opacity: 0, y: 20, scale: 0.8 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0 }}
                      className={`absolute ${event.type === 'wind' ? 'left-10 bottom-10' : 'right-10 bottom-10'} bg-black/80 border border-fuchsia-500/50 p-3 rounded-lg flex items-center gap-3 z-20`}
                    >
                      {event.type === 'wind' ? <Wind className="w-6 h-6 text-cyan-400" /> : <Droplets className="w-6 h-6 text-emerald-400" />}
                      <div>
                        <div className="text-xs font-mono font-bold text-white uppercase">IoT Trigger: {event.type}</div>
                        <div className="text-[10px] font-mono text-arkhe-muted">Target: {event.target} | Int: {event.intensity}</div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Playback Controls */}
              <div className="h-12 bg-[#111214] border-t border-fuchsia-500/20 flex items-center px-4 gap-4 shrink-0">
                <button onClick={togglePlayback} className="text-white hover:text-fuchsia-400 transition-colors">
                  {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                </button>
                
                {/* Progress Bar */}
                <div className="flex-1 h-2 bg-black rounded-full overflow-hidden border border-arkhe-border">
                  <div 
                    className="h-full bg-fuchsia-500 transition-all duration-1000 ease-linear"
                    style={{ width: `${(playbackTime / 60) * 100}%` }}
                  ></div>
                </div>
                
                <div className="text-xs font-mono text-arkhe-muted">
                  60s
                </div>
              </div>
            </div>

            {/* Bottom: Code/Architecture View */}
            <div className="flex-1 p-6 overflow-y-auto custom-scrollbar bg-[#0a0a0c]">
              <AnimatePresence mode="wait">
                {activeModule === 'ginga' && (
                  <motion.div key="ginga" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                    <div>
                      <h3 className="text-sm font-mono text-fuchsia-400 uppercase tracking-widest border-b border-fuchsia-500/20 pb-2 mb-4">Módulo 1: Ginga-Core Estendido</h3>
                      <p className="text-xs font-mono text-arkhe-muted mb-4 leading-relaxed">
                        O middleware Ginga original foi estendido para suportar a ontologia ℂ/ℤ. O parser NCL agora reconhece tags ontológicas (`&lt;sensory&gt;`, `&lt;profile&gt;`, `&lt;contract&gt;`) e as delega para o `ncl_ontology.c`.
                      </p>
                    </div>
                    
                    <div className="bg-[#111214] border border-arkhe-border rounded-lg overflow-hidden">
                      <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                        <span>src/ncl_ontology.c</span>
                        <span>C</span>
                      </div>
                      <pre className="p-4 text-[10px] font-mono text-arkhe-text overflow-x-auto">
{`int ontology_process_node(xmlNode *node) {
    if (xmlStrcmp(node->name, (const xmlChar *)"sensory") == 0) {
        xmlChar *type = xmlGetProp(node, (const xmlChar *)"type");
        xmlChar *intensity = xmlGetProp(node, (xmlChar *)"intensity");
        xmlChar *target = xmlGetProp(node, (xmlChar *)"target");
        if (type && intensity && target) {
            float f_intensity = atof((char*)intensity);
            ontology_trigger_sensory((char*)type, f_intensity, (char*)target);
        }
        xmlFree(type); xmlFree(intensity); xmlFree(target);
        return 1;
    }
    // ... profile and contract handling ...
    return 0;
}`}
                      </pre>
                    </div>
                  </motion.div>
                )}

                {activeModule === 'guarana' && (
                  <motion.div key="guarana" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                    <div>
                      <h3 className="text-sm font-mono text-fuchsia-400 uppercase tracking-widest border-b border-fuchsia-500/20 pb-2 mb-4">Módulo 3: Protocolo Guaraná-Tzinor</h3>
                      <p className="text-xs font-mono text-arkhe-muted mb-4 leading-relaxed">
                        A ponte de comunicação entre a TV e os dispositivos IoT periféricos. Utiliza WebSockets para transmitir comandos sensoriais em tempo real, sincronizados com a mídia NCL.
                      </p>
                    </div>
                    
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      <div className="bg-[#111214] border border-arkhe-border rounded-lg overflow-hidden flex flex-col">
                        <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                          <span>server/guarana_server.js</span>
                          <span>Node.js</span>
                        </div>
                        <pre className="p-4 text-[10px] font-mono text-arkhe-text overflow-x-auto flex-1">
{`wss.on('connection', (ws, req) => {
    const deviceId = req.url.split('/').pop();
    devices.set(deviceId, ws);
    logger.info(\`Device connected: \${deviceId}\`);

    ws.on('message', (message) => {
        logger.info(\`Received: \${message}\`);
    });
});`}
                        </pre>
                      </div>
                      
                      <div className="bg-[#111214] border border-arkhe-border rounded-lg overflow-hidden flex flex-col">
                        <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                          <span>client/TzinorClient.kt</span>
                          <span>Kotlin</span>
                        </div>
                        <pre className="p-4 text-[10px] font-mono text-arkhe-text overflow-x-auto flex-1">
{`override fun onMessage(ws: WebSocket, text: String) {
    println("Received: $text")
    // Parse JSON: {"effect":"wind","intensity":0.7}
    // Trigger local actuator (e.g., fan motor)
    ActuatorController.trigger(text)
}`}
                        </pre>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeModule === 'pocai' && (
                  <motion.div key="pocai" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                    <div>
                      <h3 className="text-sm font-mono text-fuchsia-400 uppercase tracking-widest border-b border-fuchsia-500/20 pb-2 mb-4">Módulo 4: PoC-AI (Proof of Consciousness)</h3>
                      <p className="text-xs font-mono text-arkhe-muted mb-4 leading-relaxed">
                        Mecanismo de recomendação retrocausal. Analisa o histórico do usuário e o conteúdo atual para prever e fazer o preload do próximo segmento de mídia, otimizando a latência.
                      </p>
                    </div>
                    
                    <div className="bg-[#111214] border border-arkhe-border rounded-lg overflow-hidden">
                      <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                        <span>poc_ai.py</span>
                        <span>Python / Flask</span>
                      </div>
                      <pre className="p-4 text-[10px] font-mono text-arkhe-text overflow-x-auto">
{`@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    user_profile = data.get('profile', {})
    current_content = data.get('current_content', '')
    user_history.append(current_content)

    features = extract_features(user_profile, user_history)
    next_content_id = model.predict([features])[0]

    preload_content(next_content_id)

    return jsonify({'next_content': next_content_id, 'preloaded': True})`}
                      </pre>
                    </div>
                  </motion.div>
                )}

                {activeModule === 'pi2' && (
                  <motion.div key="pi2" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                    <div>
                      <h3 className="text-sm font-mono text-fuchsia-400 uppercase tracking-widest border-b border-fuchsia-500/20 pb-2 mb-4">Módulo 5: Camada de Verificação π²</h3>
                      <p className="text-xs font-mono text-arkhe-muted mb-4 leading-relaxed">
                        Implementação em Rust para assinatura digital de visualizações (Proof of View). Utiliza Ed25519 para assinar eventos de visualização, garantindo a integridade dos contratos de royalties definidos no NCL.
                      </p>
                    </div>
                    
                    <div className="bg-[#111214] border border-arkhe-border rounded-lg overflow-hidden">
                      <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                        <span>src/lib.rs</span>
                        <span>Rust / FFI</span>
                      </div>
                      <pre className="p-4 text-[10px] font-mono text-arkhe-text overflow-x-auto">
{`#[no_mangle]
pub extern "C" fn pi_sign_view(viewer_id: *const c_char, content_id: *const c_char, out_len: *mut usize) -> *mut u8 {
    let viewer = unsafe { CStr::from_ptr(viewer_id).to_string_lossy().into_owned() };
    let content = unsafe { CStr::from_ptr(content_id).to_string_lossy().into_owned() };
    let timestamp = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();

    let event = ViewEvent { viewer_id: viewer, content_id: content, timestamp };
    let msg = serde_json::to_vec(&event).unwrap();

    let mut csprng = OsRng;
    let signing_key = SigningKey::generate(&mut csprng);
    let signature: Signature = signing_key.sign(&msg);
    
    // Return raw pointer to C
    // ...
}`}
                      </pre>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
