import { useState, useRef, useCallback, useEffect } from 'react';
import styled from 'styled-components';

const InputArea = styled.div`
  flex-shrink: 0;
  padding: 12px 36px 20px;
  background: ${({ theme }) => theme.colors.bg};
  border-top: 1px solid ${({ theme }) => theme.colors.borderLight};
`;

const InputRow = styled.div`
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: ${({ theme }) => theme.colors.surface};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: 10px 12px 10px 16px;
  transition: border-color 0.15s, box-shadow 0.15s;

  &:focus-within {
    border-color: ${({ theme }) => theme.colors.primary};
    box-shadow: 0 0 0 3px ${({ theme }) => `${theme.colors.primary}14`};
  }
`;

const Textarea = styled.textarea`
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font-family: inherit;
  font-size: ${({ theme }) => theme.fontSizes.md};
  color: ${({ theme }) => theme.colors.text};
  line-height: 1.5;
  min-height: 24px;
  max-height: 96px; /* ~4 lines */
  overflow-y: auto;
  padding: 0;

  &::placeholder {
    color: ${({ theme }) => theme.colors.textTertiary};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-thumb {
    background: ${({ theme }) => theme.colors.border};
    border-radius: 2px;
  }
`;

const SendButton = styled.button`
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ disabled, theme }) =>
    disabled ? theme.colors.border : theme.colors.primary};
  color: ${({ disabled }) => (disabled ? '#aaa' : '#fff')};
  cursor: ${({ disabled }) => (disabled ? 'not-allowed' : 'pointer')};
  transition: background 0.1s;

  &:not(:disabled):hover {
    background: ${({ theme }) => theme.colors.primaryHover};
  }
`;

const SendIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="7" y1="13" x2="7" y2="1" />
    <polyline points="2 6 7 1 12 6" />
  </svg>
);

function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 96)}px`;
  }, []);

  useEffect(() => {
    autoResize();
  }, [value, autoResize]);

  const handleChange = useCallback(
    (e) => {
      setValue(e.target.value);
    },
    []
  );

  const handleSend = useCallback(() => {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue('');
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <InputArea>
      <InputRow>
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your documents..."
          disabled={disabled}
          rows={1}
        />
        <SendButton
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          title="Send (Enter)"
        >
          <SendIcon />
        </SendButton>
      </InputRow>
    </InputArea>
  );
}

export default ChatInput;
