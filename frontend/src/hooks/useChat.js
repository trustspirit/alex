import { useState, useEffect, useCallback, useRef } from 'react';
import { useBridge } from './useBridge';
import { useStreaming } from './useStreaming';

function generateId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export function useChat() {
  const { call } = useBridge();
  const {
    streamingText,
    isStreaming,
    queryResult,
    queryError,
    startStreaming,
    reset: resetStreaming,
  } = useStreaming();

  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCollectionId, setSelectedCollectionId] = useState(null);
  const [collections, setCollections] = useState([]);

  // Track whether a streaming response has been committed to messages
  const streamingCommittedRef = useRef(false);
  const pendingSessionRef = useRef(null);

  // Load sessions and collections on mount
  useEffect(() => {
    async function init() {
      try {
        const [sessionList, colList] = await Promise.all([
          call('list_sessions'),
          call('list_collections'),
        ]);
        setSessions(sessionList || []);
        setCollections(colList || []);

        if (sessionList && sessionList.length > 0) {
          const first = sessionList[0];
          setCurrentSessionId(first.id);
          loadMessages(first.id);
        }
      } catch (err) {
        console.error('[useChat] init failed:', err);
      }
    }
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadMessages = useCallback(
    async (sessionId) => {
      if (!sessionId) return;
      try {
        const msgs = await call('get_messages', sessionId);
        setMessages(msgs || []);
      } catch (err) {
        console.error('[useChat] loadMessages failed:', err);
        setMessages([]);
      }
    },
    [call]
  );

  // When queryResult arrives, commit assistant message
  useEffect(() => {
    if (!queryResult || streamingCommittedRef.current) return;
    streamingCommittedRef.current = true;

    const assistantMsg = {
      id: generateId(),
      role: 'assistant',
      content: queryResult.answer || streamingText,
      sources: queryResult.sources || [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);
  }, [queryResult, streamingText]);

  // When queryError arrives, commit error message
  useEffect(() => {
    if (!queryError || streamingCommittedRef.current) return;
    streamingCommittedRef.current = true;

    const errorMsg = {
      id: generateId(),
      role: 'assistant',
      content: queryError,
      isError: true,
      sources: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, errorMsg]);
  }, [queryError]);

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || isStreaming) return;

      let sessionId = currentSessionId;

      // Create a session if none exists
      if (!sessionId) {
        try {
          const session = await call('create_session', text.slice(0, 60));
          if (session) {
            sessionId = session.id;
            setCurrentSessionId(session.id);
            setSessions((prev) => [session, ...prev]);
            pendingSessionRef.current = session.id;
          }
        } catch (err) {
          console.error('[useChat] create session failed:', err);
          return;
        }
      }

      const userMsg = {
        id: generateId(),
        role: 'user',
        content: text,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      streamingCommittedRef.current = false;
      startStreaming();
      setLoading(true);

      try {
        await call('ask', text, sessionId, selectedCollectionId);
      } catch (err) {
        console.error('[useChat] ask failed:', err);
      } finally {
        setLoading(false);
      }
    },
    [call, currentSessionId, isStreaming, selectedCollectionId, startStreaming]
  );

  const selectSession = useCallback(
    async (sessionId) => {
      if (sessionId === currentSessionId) return;
      resetStreaming();
      streamingCommittedRef.current = true;
      setCurrentSessionId(sessionId);
      await loadMessages(sessionId);
    },
    [currentSessionId, loadMessages, resetStreaming]
  );

  const createNewSession = useCallback(async () => {
    try {
      const session = await call('create_session', 'New Chat');
      if (session) {
        setSessions((prev) => [session, ...prev]);
        setCurrentSessionId(session.id);
        setMessages([]);
        resetStreaming();
        streamingCommittedRef.current = true;
      }
    } catch (err) {
      console.error('[useChat] createNewSession failed:', err);
    }
  }, [call, resetStreaming]);

  const deleteSession = useCallback(
    async (sessionId) => {
      try {
        await call('delete_session', sessionId);
        setSessions((prev) => {
          const next = prev.filter((s) => s.id !== sessionId);
          if (currentSessionId === sessionId) {
            if (next.length > 0) {
              setCurrentSessionId(next[0].id);
              loadMessages(next[0].id);
            } else {
              setCurrentSessionId(null);
              setMessages([]);
              // Create a fresh session
              call('create_session', 'New Chat').then((s) => {
                if (s) {
                  setSessions([s]);
                  setCurrentSessionId(s.id);
                }
              });
            }
          }
          return next;
        });
      } catch (err) {
        console.error('[useChat] deleteSession failed:', err);
      }
    },
    [call, currentSessionId, loadMessages]
  );

  const setCollectionFilter = useCallback((collId) => {
    setSelectedCollectionId(collId);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        createNewSession();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [createNewSession]);

  return {
    sessions,
    currentSessionId,
    messages,
    streamingText,
    isStreaming,
    queryError,
    loading,
    selectedCollectionId,
    collections,
    sendMessage,
    selectSession,
    createNewSession,
    deleteSession,
    setCollectionFilter,
  };
}
