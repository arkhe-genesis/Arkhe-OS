// frontend/src/hooks/useEcoGStream.ts
import { useState, useEffect } from 'react';

export const useEcoGStream = (participantDid: string) => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    setIsConnected(true);
    return () => setIsConnected(false);
  }, [participantDid]);

  return { isConnected };
};
