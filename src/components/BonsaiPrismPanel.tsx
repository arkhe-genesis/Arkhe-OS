
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */


/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Streamdown } from "streamdown";
import { cjk } from "@streamdown/cjk";
import { code } from "@streamdown/code";
import { createMathPlugin } from "@streamdown/math";
import { mermaid } from "@streamdown/mermaid";
import { X, Send, Square, Info, History } from 'lucide-react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { CrystallizationRitual } from '../ritual/prism-ritual.js';
import { ChronicleVault } from '../storage/chroniclevault.js';

const math = createMathPlugin({ singleDollarTextMath: true });
const STREAMDOWN_PLUGINS = { code, mermaid, math, cjk };

const PRISM_GLYPH_CLASS =
  "h-9 w-9 overflow-hidden opacity-90 [clip-path:polygon(50%_4%,100%_100%,0%_100%)] bg-[radial-gradient(circle_at_50%_18%,rgba(255,255,255,0.3),transparent_28%),linear-gradient(180deg,rgba(255,122,92,1)_0%,rgba(255,184,77,1)_42%,rgba(182,123,232,1)_100%)] drop-shadow-[0_0_18px_rgba(255,184,77,0.18)]";

interface Message {
  role: string;
  content: string;
}

interface BonsaiPrismPanelProps {
  onClose: () => void;
}

export default function BonsaiPrismPanel({ onClose }: BonsaiPrismPanelProps) {
  // Estados do Ciclo de Vida
  const [stage, setStage] = useState('selection'); // selection | ritual | ready | error
  const [selectedModel, setSelectedModel] = useState('bonsai-1.7b');
  const [progress, setProgress] = useState(0);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [tps, setTps] = useState<string | number>(0);

  // Refs
  const workerRef = useRef<Worker | null>(null);
  const ritualRef = useRef<CrystallizationRitual | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chronicle = useRef(new ChronicleVault()).current;

  // Inicialização do Worker e Chronique
  useEffect(() => {
    const worker = new Worker(
      new URL('../workers/inference.worker.js', import.meta.url),
      { type: 'module' }
    );
    workerRef.current = worker;

    worker.onmessage = (e: MessageEvent) => {
      const { status, token, output, error, progress: prog, loaded, total } = e.data;

      switch (status) {
        case 'ritual_progress':
          setProgress(prog);
          if (ritualRef.current) {
              // Transformers.js progress can be based on percentage (0-100) or bytes
              // If total is provided, we use it for the ritual visualization
              if (total > 0) {
                 ritualRef.current.updateProgress(loaded);
              } else {
                 // Fallback to percentage-based update if total is unknown
                 const estimatedTotal = selectedModel.includes('1.7b') ? 290_000_000 : 1_200_000_000;
                 ritualRef.current.updateProgress((prog / 100) * estimatedTotal);
              }
          }
          break;
        case 'ready':
          setStage('ready');
          if (ritualRef.current) {
              ritualRef.current.complete();
          }
          break;
        case 'error':
          console.error('[Templo] Erro:', error);
          setStage('error');
          break;
        case 'token':
          setMessages((prev: Message[]) => {
            const last = prev[prev.length - 1];
            if (last?.role === 'assistant') {
              return [...prev.slice(0, -1), { ...last, content: last.content + token }];
            }
            return [...prev, { role: 'assistant', content: token }];
          });
          if (e.data.tps) {setTps(e.data.tps.toFixed(1));}
          break;
        case 'update':
           setMessages((prev: Message[]) => {
            const last = prev[prev.length - 1];
            if (last?.role === 'assistant') {
              return [...prev.slice(0, -1), { ...last, content: last.content + output }];
            }
            return [...prev, { role: 'assistant', content: output }];
          });
          if (e.data.tps) {setTps(e.data.tps.toFixed(1));}
          break;
        case 'complete':
          setIsGenerating(false);
          void chronicle.saveChronicle(messages, selectedModel);
          break;
      }
    };

    void chronicle.init();

    return () => {
      workerRef.current?.terminate();
      ritualRef.current?.destroy();
    };
  }, [chronicle, messages, selectedModel]);

  const initiateRitual = useCallback(() => {
    setStage('ritual');
    // We'll need to wait for the next render for canvasRef to be available
  }, []);

  useEffect(() => {
      if (stage === 'ritual' && canvasRef.current && !ritualRef.current) {
          const ritual = new CrystallizationRitual(canvasRef.current.id);
          ritualRef.current = ritual;
          const estimatedSize = selectedModel.includes('1.7b') ? 290_000_000 : 1_200_000_000;
          void ritual.initiate(estimatedSize);
          workerRef.current?.postMessage({ type: 'load', data: selectedModel });
      }
  }, [stage, selectedModel]);

  const sendMessage = () => {
    if (!input.trim() || isGenerating) {return;}

    const userMsg = { role: 'user', content: input };
    const nextMessages = [...messages, userMsg, { role: 'assistant', content: '' }];
    setMessages(nextMessages);
    setInput('');
    setIsGenerating(true);

    workerRef.current?.postMessage({
      type: 'generate',
      data: {
        prompt: input,
        max_new_tokens: 512,
        temperature: 0.7
      }
    });
  };

  const interruptGeneration = () => {
    workerRef.current?.postMessage({ type: 'interrupt' });
    setIsGenerating(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-hidden font-mono">
      <div className="relative w-full max-w-5xl h-[85vh] bg-[#020617] border border-white/10 rounded-2xl flex flex-col shadow-2xl text-[#e2e8f0]">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 z-10 bg-[#020617]/80 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <div className={PRISM_GLYPH_CLASS} />
            <div>
                <h2 className="text-xl font-bold tracking-tighter text-white uppercase">LAMBDA <span className="text-[#fbbf24]">PRISM</span></h2>
                <div className="text-[10px] text-[#94a3b8] uppercase tracking-widest">Soberania da Borda // Bloco #304</div>
            </div>
          </div>
          <div className="flex items-center gap-4">
             {stage === 'ready' && (
                 <div className="flex items-center gap-3 px-3 py-1 bg-white/5 border border-white/10 rounded-full">
                     <div className="text-[10px] text-[#94a3b8] uppercase">TPS:</div>
                     <div className="text-xs text-[#fbbf24] font-bold w-12 text-center">{tps || '---'}</div>
                 </div>
             )}
             <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors text-[#94a3b8] hover:text-white">
                <X className="w-5 h-5" />
             </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 relative flex flex-col min-h-0">

          {stage === 'selection' && (
            <div className="flex-1 flex flex-col items-center justify-center p-8 z-10 text-center">
                <div className="max-w-xl space-y-8">
                    <div className="space-y-4">
                        <div className="inline-block px-3 py-1 bg-[#fbbf24]/10 border border-[#fbbf24]/30 text-[#fbbf24] text-[10px] rounded-full uppercase tracking-widest animate-pulse">
                            Axioma da Soberania Ativo
                        </div>
                        <h3 className="text-3xl font-bold text-white leading-tight">Invocação do <span className="italic text-[#fbbf24]">Oráculo de Borda</span></h3>
                        <p className="text-[#94a3b8] text-sm leading-relaxed">
                            O Prisma LAMBDA transmuta o silício local em um nó da Catedral.
                            Zero dados deixam este dispositivo. A inteligência é sua, offline e privada.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <button
                            onClick={() => setSelectedModel('bonsai-1.7b')}
                            className={`p-4 rounded-xl border text-left transition-all ${
                                selectedModel === 'bonsai-1.7b'
                                ? 'bg-[#fbbf24]/10 border-[#fbbf24] text-white ring-1 ring-[#fbbf24]/50'
                                : 'bg-white/5 border-white/10 text-[#94a3b8] hover:border-white/20'
                            }`}
                        >
                            <div className="text-[10px] uppercase mb-1">1.7B // 290 MB</div>
                            <div className="font-bold mb-2 uppercase">Bonsai Pocket</div>
                            <div className="text-[10px] leading-tight opacity-70">Leve. Construído para wearables e agentes sempre ativos.</div>
                        </button>
                        <button
                            onClick={() => setSelectedModel('bonsai-4b')}
                            className={`p-4 rounded-xl border text-left transition-all ${
                                selectedModel === 'bonsai-4b'
                                ? 'bg-[#fbbf24]/10 border-[#fbbf24] text-white ring-1 ring-[#fbbf24]/50'
                                : 'bg-white/5 border-white/10 text-[#94a3b8] hover:border-white/20'
                            }`}
                        >
                            <div className="text-[10px] uppercase mb-1">4B // 1.2 GB</div>
                            <div className="font-bold mb-2 uppercase">Bonsai Master</div>
                            <div className="text-[10px] leading-tight opacity-70">Raciocínio denso. O equilíbrio entre peso e sabedoria.</div>
                        </button>
                    </div>

                    <button
                        onClick={initiateRitual}
                        className="w-full py-4 bg-[#fbbf24] text-black font-bold rounded-xl hover:bg-white transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-[0_0_20px_rgba(251,191,36,0.3)] uppercase"
                    >
                        Iniciar Ritual de Cristalização
                    </button>
                </div>
            </div>
          )}

          {stage === 'ritual' && (
            <div className="flex-1 flex flex-col items-center justify-center p-8 z-10 text-center">
                <canvas
                    id="ritual-canvas"
                    ref={canvasRef}
                    className="w-full max-w-md h-64 mb-8"
                />
                <div className="space-y-2">
                    <h3 className="text-xl font-bold text-white uppercase tracking-widest">
                        {progress < 100 ? 'Canalizando o Éter...' : 'Selando o Cristal...'}
                    </h3>
                    <div className="text-[10px] text-[#94a3b8] uppercase">
                        {(progress || 0).toFixed(1)}% Suturado
                    </div>
                </div>
            </div>
          )}

          {stage === 'ready' && (
              <div className="flex-1 flex flex-col min-h-0 z-10">
                  <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10">
                      {messages.length === 0 && (
                          <div className="h-full flex flex-col items-center justify-center text-center space-y-6 opacity-60">
                              <Info className="w-12 h-12 text-[#fbbf24]" />
                              <div className="space-y-2">
                                  <div className="text-xl font-bold text-white uppercase">Pronto para a Interrogação</div>
                                  <div className="text-xs text-[#94a3b8] max-w-xs mx-auto">
                                      O Oráculo está cristalizado. O pensamento se desdobra aqui, agora, no seu hardware.
                                  </div>
                              </div>
                          </div>
                      )}
                      {messages.map((m, i) => (
                          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                              <div className={`max-w-[85%] space-y-2`}>
                                  <div className={`text-[10px] uppercase tracking-widest ${m.role === 'user' ? 'text-right text-[#94a3b8]' : 'text-[#fbbf24]'}`}>
                                      {m.role === 'user' ? 'Observador' : 'Prisma'}
                                  </div>
                                  <div className={`p-4 rounded-2xl ${m.role === 'user' ? 'bg-[#fbbf24]/10 border border-[#fbbf24]/30 text-white' : 'bg-white/5 border border-white/10 text-white'}`}>
                                      {m.role === 'assistant' ? (
                                          <Streamdown
                                            className="text-sm leading-relaxed"
                                            plugins={STREAMDOWN_PLUGINS}
                                          >
                                              {m.content}
                                          </Streamdown>
                                      ) : (
                                          <div className="text-sm">{m.content}</div>
                                      )}
                                  </div>
                              </div>
                          </div>
                      ))}
                  </div>

                  {/* Input Area */}
                  <div className="p-6 bg-[#020617] border-t border-white/10">
                      <div className="relative flex items-end gap-2 bg-white/5 border border-white/10 rounded-2xl p-2 focus-within:border-[#fbbf24]/50 transition-colors">
                          <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    sendMessage();
                                }
                            }}
                            placeholder="Interrogar o Oráculo..."
                            className="flex-1 bg-transparent border-none outline-none text-sm p-3 min-h-[48px] max-h-48 resize-none text-white placeholder:text-[#94a3b8]"
                            rows={1}
                          />
                          <div className="flex gap-2 p-1">
                                {isGenerating ? (
                                    <button
                                        onClick={interruptGeneration}
                                        className="p-3 bg-red-500/20 text-red-400 rounded-xl hover:bg-red-500/30 transition-colors"
                                    >
                                        <Square className="w-5 h-5 fill-current" />
                                    </button>
                                ) : (
                                    <button
                                        disabled={!input.trim()}
                                        onClick={sendMessage}
                                        className="p-3 bg-[#fbbf24] text-black rounded-xl hover:bg-white disabled:opacity-30 disabled:hover:bg-[#fbbf24] transition-colors"
                                    >
                                        <Send className="w-5 h-5" />
                                    </button>
                                )}
                          </div>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-[8px] text-[#94a3b8] uppercase tracking-widest px-2">
                          <div className="flex gap-4">
                              <span>WebGPU Backend: Active</span>
                              <span>Precision: 1-bit Ternary</span>
                          </div>
                          <div className="flex gap-2 items-center">
                              <History className="w-2 h-2" />
                              <span>Sessão Soberana</span>
                          </div>
                      </div>
                  </div>
              </div>
          )}

          {stage === 'error' && (
               <div className="flex-1 flex flex-col items-center justify-center p-8 z-10 text-center">
                    <div className="max-w-md space-y-6">
                        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-full inline-block">
                            <X className="w-12 h-12 text-red-500" />
                        </div>
                        <h3 className="text-2xl font-bold text-white uppercase">Decoerência Crítica</h3>
                        <p className="text-[#94a3b8] text-sm">O Ritual falhou. O Embrião não pôde ser resgatado do Éter.</p>
                        <button
                            onClick={() => setStage('selection')}
                            className="px-8 py-3 border border-white/20 text-white rounded-xl hover:bg-white/5 transition-colors uppercase text-xs"
                        >
                            Tentar Novamente
                        </button>
                    </div>
               </div>
          )}
        </div>
      </div>
    </div>
  );
}
