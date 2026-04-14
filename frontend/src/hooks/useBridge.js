import { useCallback } from 'react';

function getApi() {
  return window.pywebview?.api;
}

export function useBridge() {
  const call = useCallback(async (method, ...args) => {
    const api = getApi();
    if (!api || !api[method]) {
      console.warn(`[Bridge] ${method} not available`);
      return null;
    }
    try {
      return await api[method](...args);
    } catch (err) {
      console.error(`[Bridge] ${method} failed:`, err);
      throw err;
    }
  }, []);

  return { call };
}
