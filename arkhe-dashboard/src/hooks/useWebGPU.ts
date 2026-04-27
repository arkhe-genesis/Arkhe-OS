// arkhe-dashboard/src/hooks/useWebGPU.ts
import { useEffect, useState, useRef } from 'react';

export function useWebGPU() {
  const [isSupported, setIsSupported] = useState(false);
  const [device, setDevice] = useState<GPUDevice | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'gpu' in navigator) {
      navigator.gpu.requestAdapter().then(adapter => {
        if (adapter) {
          adapter.requestDevice().then(dev => {
            setDevice(dev);
            setIsSupported(true);
          });
        }
      });
    }
  }, []);

  return { isSupported, device };
}
