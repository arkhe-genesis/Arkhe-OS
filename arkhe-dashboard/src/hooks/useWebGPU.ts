
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/hooks/useWebGPU.ts
/* eslint-disable @typescript-eslint/no-unused-vars, @typescript-eslint/no-floating-promises */

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
