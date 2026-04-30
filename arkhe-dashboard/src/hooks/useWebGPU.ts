
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/hooks/useWebGPU.ts
import { useEffect, useState, _useRef } from 'react';

export function useWebGPU() {
  const [isSupported, setIsSupported] = useState(false);
  const [device, setDevice] = useState<GPUDevice | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'gpu' in navigator) {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
      navigator.gpu.requestAdapter().then(adapter => {

        if (adapter) {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
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
