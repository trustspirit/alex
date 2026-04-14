import { useState, useCallback } from 'react';
import styled, { keyframes } from 'styled-components';
import SourceCard from './SourceCard';

// ---------------------------------------------------------------------------
// Minimal markdown renderer
// ---------------------------------------------------------------------------

function renderMarkdown(text) {
  if (!text) return [];
  const lines = text.split('\n');
  const result = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code blocks
    if (line.startsWith('```')) {
      const lang = line.slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      result.push({ type: 'code', content: codeLines.join('\n'), lang });
      i++;
      continue;
    }

    // Headings
    const headingMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (headingMatch) {
      result.push({ type: `h${headingMatch[1].length}`, content: headingMatch[2] });
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

    // Normal paragraph
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
              {block.lang && <CodeLang>{block.lang}</CodeLang>}
              <code>{block.content}</code>
            </CodeBlock>
          );
        }
        if (block.type === 'h1') return <Heading1 key={idx}><InlineContent text={block.content} /></Heading1>;
        if (block.type === 'h2') return <Heading2 key={idx}><InlineContent text={block.content} /></Heading2>;
        if (block.type === 'h3') return <Heading3 key={idx}><InlineContent text={block.content} /></Heading3>;
        if (block.type === 'h4') return <Heading4 key={idx}><InlineContent text={block.content} /></Heading4>;
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
        if (block.type === 'br') return <Spacer key={idx} />;
        return (
          <Paragraph key={idx}>
            <InlineContent text={block.content} />
          </Paragraph>
        );
      })}
    </>
  );
}

// ---------------------------------------------------------------------------
// Styled Components — Claude/ChatGPT style
// ---------------------------------------------------------------------------

const blink = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
`;

const MessageRow = styled.div`
  display: flex;
  padding: 24px 0;
  border-bottom: 1px solid ${({ theme }) => theme.colors.borderLight};

  &:last-child {
    border-bottom: none;
  }
`;

/* Avatar removed — only sender name is shown */

const MessageBody = styled.div`
  flex: 1;
  min-width: 0;
  user-select: text;
  cursor: text;
`;

const SenderName = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text};
  margin-bottom: 6px;
`;

const Content = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.md};
  line-height: 1.7;
  color: ${({ $isError, theme }) => $isError ? theme.colors.error : theme.colors.text};

  p + p, p + ul, p + ol, ul + p, ol + p {
    margin-top: 0.6em;
  }
`;

const Paragraph = styled.p`
  margin: 0;
`;

const Spacer = styled.div`
  height: 0.5em;
`;

const Heading1 = styled.h1`
  font-size: 1.3em;
  font-weight: 700;
  margin: 0.8em 0 0.4em;
  &:first-child { margin-top: 0; }
`;

const Heading2 = styled.h2`
  font-size: 1.15em;
  font-weight: 700;
  margin: 0.7em 0 0.3em;
  &:first-child { margin-top: 0; }
`;

const Heading3 = styled.h3`
  font-size: 1em;
  font-weight: 600;
  margin: 0.6em 0 0.25em;
  &:first-child { margin-top: 0; }
`;

const Heading4 = styled.h4`
  font-size: 0.95em;
  font-weight: 600;
  margin: 0.5em 0 0.2em;
  &:first-child { margin-top: 0; }
`;

const InlineCode = styled.code`
  font-family: ${({ theme }) => theme.fonts.mono};
  font-size: 0.85em;
  background: ${({ theme }) => theme.colors.bg};
  border: 1px solid ${({ theme }) => theme.colors.borderLight};
  padding: 2px 6px;
  border-radius: 4px;
`;

const CodeBlock = styled.pre`
  font-family: ${({ theme }) => theme.fonts.mono};
  font-size: 0.8125rem;
  background: #1E1E1E;
  color: #D4D4D4;
  border-radius: 8px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 0.6em 0;
  line-height: 1.5;
  position: relative;

  code {
    font-family: inherit;
    font-size: inherit;
    background: none;
    border: none;
    padding: 0;
    color: inherit;
  }
`;

const CodeLang = styled.span`
  position: absolute;
  top: 8px;
  right: 12px;
  font-size: 11px;
  color: #888;
  text-transform: lowercase;
`;

const StyledUl = styled.ul`
  margin: 0.4em 0;
  padding-left: 1.5em;
  li { margin-top: 0.3em; line-height: 1.6; }
`;

const StyledOl = styled.ol`
  margin: 0.4em 0;
  padding-left: 1.6em;
  li { margin-top: 0.3em; line-height: 1.6; }
`;

const Cursor = styled.span`
  display: inline-block;
  width: 2px;
  height: 1em;
  background: ${({ theme }) => theme.colors.primary};
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: ${blink} 0.8s step-start infinite;
`;

const SourceToggle = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: none;
  padding: 8px 0 0;
  color: ${({ theme }) => theme.colors.textTertiary};
  font-size: ${({ theme }) => theme.fontSizes.xs};
  cursor: pointer;
  font-family: inherit;
  transition: color 0.15s;

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

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

function MessageBubble({ message, streamingText, isStreaming }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const toggleSources = useCallback(() => setSourcesOpen((v) => !v), []);

  const isUser = message?.role === 'user';
  const isError = message?.isError;

  // Streaming placeholder
  if (!message && isStreaming) {
    return (
      <MessageRow>
          <MessageBody>
          <SenderName>Alex</SenderName>
          <Content>
            <MarkdownContent text={streamingText || ''} />
            <Cursor />
          </Content>
        </MessageBody>
      </MessageRow>
    );
  }

  if (!message) return null;

  const sources = message.sources || [];
  const hasSources = sources.length > 0;

  return (
    <MessageRow>
      <MessageBody>
        <SenderName>{isUser ? 'You' : 'Alex'}</SenderName>
        <Content $isError={isError}>
          {isError ? message.content : <MarkdownContent text={message.content} />}
        </Content>

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
      </MessageBody>
    </MessageRow>
  );
}

export default MessageBubble;
