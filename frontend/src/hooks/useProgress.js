import { useState, useEffect, useCallback } from 'react';

export function useProgress() {
  const [progress, setProgress] = useState({});  // { [doc_id]: { step, percent } }
  const [warnings, setWarnings] = useState([]);
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    if (!window.__bridge__) window.__bridge__ = {};

    window.__bridge__.onIngestProgress = (data) => {
      setProgress(prev => ({
        ...prev,
        [data.doc_id]: { step: data.step, percent: data.percent },
      }));
    };
    window.__bridge__.onIngestWarning = (data) => {
      setWarnings(prev => [...prev, { doc_id: data.doc_id, warning: data.warning, id: Date.now() }]);
    };
    window.__bridge__.onIngestError = (data) => {
      setErrors(prev => [...prev, { doc_id: data.doc_id, error: data.error, id: Date.now() }]);
    };

    return () => {
      delete window.__bridge__.onIngestProgress;
      delete window.__bridge__.onIngestWarning;
      delete window.__bridge__.onIngestError;
    };
  }, []);

  const dismissWarning = useCallback((id) => {
    setWarnings(prev => prev.filter(w => w.id !== id));
  }, []);

  const dismissError = useCallback((id) => {
    setErrors(prev => prev.filter(e => e.id !== id));
  }, []);

  return { progress, warnings, errors, dismissWarning, dismissError };
}
