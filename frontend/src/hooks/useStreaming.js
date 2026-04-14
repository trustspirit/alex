import { useState, useEffect, useCallback } from 'react';

export function useStreaming() {
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [queryError, setQueryError] = useState(null);

  useEffect(() => {
    if (!window.__bridge__) window.__bridge__ = {};

    window.__bridge__.onToken = (data) => {
      setStreamingText(prev => prev + data.token);
    };
    window.__bridge__.onQueryComplete = (data) => {
      setQueryResult(data);
      setIsStreaming(false);
    };
    window.__bridge__.onQueryError = (data) => {
      setQueryError(data.error);
      setIsStreaming(false);
    };

    return () => {
      delete window.__bridge__.onToken;
      delete window.__bridge__.onQueryComplete;
      delete window.__bridge__.onQueryError;
    };
  }, []);

  const startStreaming = useCallback(() => {
    setStreamingText('');
    setQueryResult(null);
    setQueryError(null);
    setIsStreaming(true);
  }, []);

  const reset = useCallback(() => {
    setStreamingText('');
    setQueryResult(null);
    setQueryError(null);
    setIsStreaming(false);
  }, []);

  return { streamingText, isStreaming, queryResult, queryError, startStreaming, reset };
}
