import { useState, useEffect, useCallback } from 'react';
import { useBridge } from './useBridge';

// Module-level state to share across all useSync instances
let globalCallbacksRegistered = false;
const listeners = new Set();

function notifyListeners(type, data) {
  listeners.forEach((listener) => listener(type, data));
}

function registerGlobalCallbacks() {
  if (globalCallbacksRegistered) return;
  globalCallbacksRegistered = true;

  if (!window.__bridge__) window.__bridge__ = {};

  window.__bridge__.onSyncStart = () => notifyListeners('start', {});
  window.__bridge__.onSyncComplete = (data) => {
    notifyListeners('complete', data);
    window.dispatchEvent(new CustomEvent('alex-sync-complete', { detail: data }));
  };
  window.__bridge__.onSyncError = (error) => {
    notifyListeners('error', error);
    if (error && error.doc_id) {
      window.dispatchEvent(new CustomEvent('alex-sync-doc-error', {
        detail: { doc_id: error.doc_id, message: error.message },
      }));
    }
  };
}

export function useSync() {
  const { call } = useBridge();
  const [syncStatus, setSyncStatus] = useState('disabled');
  const [lastSyncedAt, setLastSyncedAt] = useState(null);
  const [syncError, setSyncError] = useState(null);

  useEffect(() => {
    call('get_sync_status').then((status) => {
      if (status && status.enabled) {
        setSyncStatus('idle');
      }
    });

    registerGlobalCallbacks();

    const listener = (type, data) => {
      if (type === 'start') {
        setSyncStatus('syncing');
        setSyncError(null);
      } else if (type === 'complete') {
        setSyncStatus('idle');
        setLastSyncedAt(new Date().toISOString());
      } else if (type === 'error') {
        setSyncStatus('error');
        setSyncError(data);
      }
    };

    listeners.add(listener);
    return () => listeners.delete(listener);
  }, [call]);

  const triggerSync = useCallback(() => {
    call('trigger_sync');
  }, [call]);

  const testConnection = useCallback(async () => {
    return await call('test_sync_connection');
  }, [call]);

  return { syncStatus, lastSyncedAt, syncError, triggerSync, testConnection };
}
