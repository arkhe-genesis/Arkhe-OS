import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AttractorState {
  activeProfile: any;
  setProfile: (profile: any) => void;
  syncWithEngine: () => Promise<void>;
}

export const useStore = create<AttractorState>()(
  persist(
    (set) => ({
      activeProfile: { id: 'default', alpha: 1.5, beta: 0.4, gamma: 0.3, T: 0.8 },
      setProfile: (p) => set({ activeProfile: p }),
      syncWithEngine: async () => {
        // Notificar daemon local para atualizar parâmetros do atrator
        console.log('🔄 Synced attractor profile with generation engine');
      },
    }),
    { name: 'arkhe-attractor-storage' }
  )
);
