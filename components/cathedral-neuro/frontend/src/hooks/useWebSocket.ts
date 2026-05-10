// frontend/src/hooks/useWebSocket.ts
import { useState, useEffect } from 'react';

export const useWebSocket = (endpoint: string) => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Simulação de conexão WebSocket
    setIsConnected(true);
    return () => setIsConnected(false);
  }, [endpoint]);

  return { isConnected };
};
