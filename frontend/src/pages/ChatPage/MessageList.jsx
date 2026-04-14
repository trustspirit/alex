import { useEffect, useRef } from 'react';
import styled, { keyframes } from 'styled-components';
import MessageBubble from './MessageBubble';

const pulse = keyframes`
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
`;

const Container = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 32px 36px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  scroll-behavior: smooth;

  /* Scrollbar styling */
  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.colors.border};
    border-radius: 3px;
  }
`;

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: ${({ theme }) => theme.colors.textTertiary};
  padding-bottom: 80px;
`;

const EmptyTitle = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 500;
  color: ${({ theme }) => theme.colors.textSecondary};
`;

const EmptySubtitle = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  text-align: center;
  max-width: 320px;
  line-height: 1.6;
`;

const LoadingDots = styled.div`
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 16px 0 8px;
`;

const Dot = styled.span`
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: ${({ theme }) => theme.colors.textTertiary};
  animation: ${pulse} 1.2s ease-in-out infinite;
  animation-delay: ${({ $delay }) => $delay || '0s'};
`;

const SpacerBottom = styled.div`
  height: 8px;
  flex-shrink: 0;
`;

function MessageList({ messages, streamingText, isStreaming, queryError, loading }) {
  const bottomRef = useRef(null);
  const prevCountRef = useRef(0);

  useEffect(() => {
    const count = messages.length;
    if (count !== prevCountRef.current || isStreaming) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      prevCountRef.current = count;
    }
  }, [messages, isStreaming, streamingText]);

  const showStreaming = isStreaming;
  const showLoading = loading && !isStreaming;

  if (messages.length === 0 && !showStreaming && !showLoading) {
    return (
      <Container>
        <EmptyState>
          <EmptyTitle>Ask anything</EmptyTitle>
          <EmptySubtitle>
            Ask questions about your uploaded documents. Alex will find relevant information and cite its sources.
          </EmptySubtitle>
        </EmptyState>
        <div ref={bottomRef} />
      </Container>
    );
  }

  return (
    <Container>
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {showLoading && (
        <LoadingDots>
          <Dot $delay="0s" />
          <Dot $delay="0.2s" />
          <Dot $delay="0.4s" />
        </LoadingDots>
      )}

      {showStreaming && (
        <MessageBubble
          message={null}
          streamingText={streamingText}
          isStreaming={isStreaming}
        />
      )}

      <SpacerBottom />
      <div ref={bottomRef} />
    </Container>
  );
}

export default MessageList;
