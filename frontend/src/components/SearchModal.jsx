import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useBridge } from '../hooks/useBridge';

const Backdrop = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  z-index: 1000;
`;

const Modal = styled.div`
  background: #fff;
  border-radius: 10px;
  width: 100%;
  max-width: 560px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  max-height: 60vh;
`;

const InputRow = styled.div`
  display: flex;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid ${({ theme }) => theme.colors.borderLight};
  gap: 10px;
`;

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#999" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
    <circle cx="7" cy="7" r="5" />
    <line x1="11" y1="11" x2="14" y2="14" />
  </svg>
);

const Input = styled.input`
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  color: ${({ theme }) => theme.colors.text};
  background: transparent;

  &::placeholder {
    color: ${({ theme }) => theme.colors.textTertiary};
  }
`;

const Shortcut = styled.span`
  font-size: 0.6875rem;
  color: ${({ theme }) => theme.colors.textTertiary};
  background: ${({ theme }) => theme.colors.bg};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 4px;
  padding: 2px 6px;
  white-space: nowrap;
`;

const Results = styled.div`
  overflow-y: auto;
  padding: 6px 0;
`;

const SectionLabel = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: ${({ theme }) => theme.colors.textTertiary};
  padding: 8px 18px 4px;
`;

const ResultItem = styled.button`
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 18px;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.text};
  transition: background 0.1s;

  &:hover {
    background: ${({ theme }) => theme.colors.surfaceHover};
  }
`;

const ResultType = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textTertiary};
  flex-shrink: 0;
`;

const EmptyText = styled.div`
  padding: 24px 18px;
  text-align: center;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textTertiary};
`;

function SearchModal({ onClose }) {
  const { call } = useBridge();
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState([]);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    async function load() {
      const [docs, chats] = await Promise.all([
        call('list_documents'),
        call('list_sessions'),
      ]);
      setDocuments(docs || []);
      setSessions(chats || []);
    }
    load();
  }, [call]);

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus();
  }, []);

  const lowerQuery = query.toLowerCase().trim();

  const filteredDocs = lowerQuery
    ? documents.filter((d) => (d.title || '').toLowerCase().includes(lowerQuery))
    : [];

  const filteredSessions = lowerQuery
    ? sessions.filter((s) => (s.title || '').toLowerCase().includes(lowerQuery))
    : [];

  const hasResults = filteredDocs.length > 0 || filteredSessions.length > 0;

  function handleSelect(type) {
    if (type === 'doc') {
      navigate('/learn');
    } else {
      navigate('/chat');
    }
    onClose();
  }

  function handleBackdropClick(e) {
    if (e.target === e.currentTarget) onClose();
  }

  return (
    <Backdrop onClick={handleBackdropClick}>
      <Modal>
        <InputRow>
          <SearchIcon />
          <Input
            ref={inputRef}
            placeholder="Search documents and chats..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Shortcut>ESC</Shortcut>
        </InputRow>

        <Results>
          {!lowerQuery && (
            <EmptyText>Type to search across documents and chats</EmptyText>
          )}

          {lowerQuery && !hasResults && (
            <EmptyText>No results found</EmptyText>
          )}

          {filteredDocs.length > 0 && (
            <>
              <SectionLabel>Documents</SectionLabel>
              {filteredDocs.slice(0, 8).map((doc) => (
                <ResultItem key={`doc-${doc.id}`} onClick={() => handleSelect('doc')}>
                  {doc.title || 'Untitled'}
                  <ResultType>{doc.source_type}</ResultType>
                </ResultItem>
              ))}
            </>
          )}

          {filteredSessions.length > 0 && (
            <>
              <SectionLabel>Chats</SectionLabel>
              {filteredSessions.slice(0, 8).map((s) => (
                <ResultItem key={`chat-${s.id}`} onClick={() => handleSelect('chat')}>
                  {s.title || 'Untitled'}
                </ResultItem>
              ))}
            </>
          )}
        </Results>
      </Modal>
    </Backdrop>
  );
}

export default SearchModal;
