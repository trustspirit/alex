import { useState, useEffect, useCallback } from 'react';
import { useBridge } from './useBridge';

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

    if (!window.__bridge__) window.__bridge__ = {};

    window.__bridge__.onSyncStart = () => {
      setSyncStatus('syncing');
      setSyncError(null);
    };

    window.__bridge__.onSyncComplete = (data) => {
      setSyncStatus('idle');
      setLastSyncedAt(new Date().toISOString());
      window.dispatchEvent(new CustomEvent('alex-sync-complete', { detail: data }));
    };

    window.__bridge__.onSyncError = (error) => {
      setSyncStatus('error');
      setSyncError(error);

      if (error && error.doc_id) {
        window.dispatchEvent(new CustomEvent('alex-sync-doc-error', {
          detail: { doc_id: error.doc_id, message: error.message },
        }));
      }
    };
  }, [call]);

  const triggerSync = useCallback(() => {
    call('trigger_sync');
  }, [call]);

  const testConnection = useCallback(async () => {
    return await call('test_sync_connection');
  }, [call]);

  return { syncStatus, lastSyncedAt, syncError, triggerSync, testConnection };
}
