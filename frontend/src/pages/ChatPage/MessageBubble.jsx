import { useState, useCallback } from 'react';
import styled, { keyframes, css } from 'styled-components';
import SourceCard from './SourceCard';

// Minimal markdown rendering: bold, inline code, code blocks, simple lists
function renderMarkdown(text) {
  if (!text) return [];

  const lines = text.split('\n');
  const result = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code blocks
    if (line.startsWith('```')) {
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      result.push({ type: 'code', content: codeLines.join('\n') });
      i++;
      continue;
    }

    // Unordered list
    if (/^[-*]\s/.test(line)) {
      const items = [];
      while (i < lines.length && /^[-*]\s/.test(lines[i])) {
        items.push(lines[i].slice(2));
        i++;
      }
      result.push({ type: 'ul', items });
      continue;
    }

    // Ordered list
    if (/^\d+\.\s/.test(line)) {
      const items = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s/, ''));
        i++;
      }
      result.push({ type: 'ol', items });
      continue;
    }

    // Blank line
    if (line.trim() === '') {
      result.push({ type: 'br' });
      i++;
      continue;
    }

    // Normal paragraph text
    result.push({ type: 'p', content: line });
    i++;
  }

  return result;
}

function inlineFormat(text) {
  const parts = [];
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) {
      parts.push({ type: 'text', content: text.slice(last, match.index) });
    }
    const raw = match[0];
    if (raw.startsWith('`')) {
      parts.push({ type: 'code', content: raw.slice(1, -1) });
    } else if (raw.startsWith('**')) {
      parts.push({ type: 'bold', content: raw.slice(2, -2) });
    } else {
      parts.push({ type: 'italic', content: raw.slice(1, -1) });
    }
    last = match.index + raw.length;
  }

  if (last < text.length) {
    parts.push({ type: 'text', content: text.slice(last) });
  }

  return parts;
}

function InlineContent({ text }) {
  const parts = inlineFormat(text);
  return (
    <>
      {parts.map((p, idx) => {
        if (p.type === 'bold') return <strong key={idx}>{p.content}</strong>;
        if (p.type === 'italic') return <em key={idx}>{p.content}</em>;
        if (p.type === 'code') return <InlineCode key={idx}>{p.content}</InlineCode>;
        return <span key={idx}>{p.content}</span>;
      })}
    </>
  );
}

function MarkdownContent({ text }) {
  const blocks = renderMarkdown(text);
  return (
    <>
      {blocks.map((block, idx) => {
        if (block.type === 'code') {
          return (
            <CodeBlock key={idx}>
              <code>{block.content}</code>
            </CodeBlock>
          );
        }
        if (block.type === 'ul') {
          return (
            <StyledUl key={idx}>
              {block.items.map((item, j) => (
                <li key={j}><InlineContent text={item} /></li>
              ))}
            </StyledUl>
          );
        }
        if (block.type === 'ol') {
          return (
            <StyledOl key={idx}>
              {block.items.map((item, j) => (
                <li key={j}><InlineContent text={item} /></li>
              ))}
            </StyledOl>
          );
        }
        if (block.type === 'br') {
          return <div key={idx} style={{ height: '0.5em' }} />;
        }
        return (
          <p key={idx} style={{ margin: 0 }}>
            <InlineContent text={block.content} />
          </p>
        );
      })}
    </>
  );
}

const blink = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
`;

const MessageRow = styled.div`
  display: flex;
  justify-content: ${({ $isUser }) => ($isUser ? 'flex-end' : 'flex-start')};
  padding: 4px 0;
`;

const BubbleWrap = styled.div`
  max-width: 720px;
  min-width: 60px;
  ${({ $isUser }) => $isUser && css`min-width: 100px;`}
`;

const Bubble = styled.div`
  padding: 12px 16px;
  border-radius: ${({ theme }) => theme.radii.lg};
  background: ${({ $isUser, theme }) =>
    $isUser ? '#EFF6FF' : theme.colors.surface};
  border: 1px solid ${({ $isUser, theme }) =>
    $isUser ? '#DBEAFE' : theme.colors.border};
  font-size: ${({ theme }) => theme.fontSizes.md};
  line-height: 1.6;
  color: ${({ $isError, theme }) => ($isError ? theme.colors.error : theme.colors.text)};

  p + p,
  p + ul,
  p + ol,
  ul + p,
  ol + p {
    margin-top: 0.6em;
  }
`;

const InlineCode = styled.code`
  font-family: ${({ theme }) => theme.fonts.mono};
  font-size: 0.85em;
  background: ${({ theme }) => theme.colors.bg};
  border: 1px solid ${({ theme }) => theme.colors.borderLight};
  padding: 1px 5px;
  border-radius: 3px;
`;

const CodeBlock = styled.pre`
  font-family: ${({ theme }) => theme.fonts.mono};
  font-size: 0.8125rem;
  background: ${({ theme }) => theme.colors.bg};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  padding: 12px 14px;
  overflow-x: auto;
  margin: 0.5em 0;
  line-height: 1.5;

  code {
    font-family: inherit;
    font-size: inherit;
    background: none;
    border: none;
    padding: 0;
  }
`;

const StyledUl = styled.ul`
  margin: 0.4em 0;
  padding-left: 1.4em;
  li + li { margin-top: 0.25em; }
`;

const StyledOl = styled.ol`
  margin: 0.4em 0;
  padding-left: 1.6em;
  li + li { margin-top: 0.25em; }
`;

const Cursor = styled.span`
  display: inline-block;
  width: 2px;
  height: 1em;
  background: ${({ theme }) => theme.colors.text};
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: ${blink} 0.9s step-start infinite;
`;

const SourceToggle = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: none;
  padding: 5px 0 0;
  color: ${({ theme }) => theme.colors.textSecondary};
  font-size: ${({ theme }) => theme.fontSizes.xs};
  cursor: pointer;
  font-family: inherit;
  transition: color 0.1s;

  &:hover {
    color: ${({ theme }) => theme.colors.text};
  }

  svg {
    transition: transform 0.15s;
    transform: ${({ $open }) => ($open ? 'rotate(180deg)' : 'rotate(0deg)')};
  }
`;

const SourceList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
`;

const ChevronIcon = () => (
  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="2 3.5 5 6.5 8 3.5" />
  </svg>
);

function MessageBubble({ message, streamingText, isStreaming }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const toggleSources = useCallback(() => setSourcesOpen((v) => !v), []);

  const isUser = message?.role === 'user';
  const isError = message?.isError;

  // Streaming placeholder bubble
  if (!message && isStreaming) {
    return (
      <MessageRow $isUser={false}>
        <BubbleWrap>
          <Bubble>
            {streamingText || ''}
            <Cursor />
          </Bubble>
        </BubbleWrap>
      </MessageRow>
    );
  }

  if (!message) return null;

  const sources = message.sources || [];
  const hasSources = sources.length > 0;

  return (
    <MessageRow $isUser={isUser}>
      <BubbleWrap $isUser={isUser}>
        <Bubble $isUser={isUser} $isError={isError}>
          {isError ? (
            message.content
          ) : (
            <MarkdownContent text={message.content} />
          )}
        </Bubble>

        {!isUser && hasSources && (
          <div>
            <SourceToggle $open={sourcesOpen} onClick={toggleSources}>
              <ChevronIcon />
              {sources.length} {sources.length === 1 ? 'source' : 'sources'}
            </SourceToggle>

            {sourcesOpen && (
              <SourceList>
                {sources.map((src, idx) => (
                  <SourceCard key={src.chunk_id || idx} source={src} />
                ))}
              </SourceList>
            )}
          </div>
        )}
      </BubbleWrap>
    </MessageRow>
  );
}

export default MessageBubble;
