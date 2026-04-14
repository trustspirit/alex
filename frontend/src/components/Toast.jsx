import { useState, useEffect, useCallback } from 'react';
import styled, { keyframes, css } from 'styled-components';

const slideIn = keyframes`
  from {
    transform: translateX(110%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
`;

const slideOut = keyframes`
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(110%);
    opacity: 0;
  }
`;

const Container = styled.div`
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
`;

function getBorderColor(type, theme) {
  if (type === 'warning') return theme.colors.warning;
  if (type === 'error') return theme.colors.error;
  return theme.colors.border;
}

function getBackground(type, theme) {
  if (type === 'warning') return theme.colors.warningBg;
  if (type === 'error') return theme.colors.errorBg;
  return theme.colors.surface;
}

const Item = styled.div`
  pointer-events: all;
  min-width: 260px;
  max-width: 360px;
  padding: 12px 14px;
  border-radius: ${({ theme }) => theme.radii.md};
  border: 1px solid ${({ type, theme }) => getBorderColor(type, theme)};
  background: ${({ type, theme }) => getBackground(type, theme)};
  box-shadow: ${({ theme }) => theme.shadows.md};
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  animation: ${({ exiting }) =>
    exiting
      ? css`${slideOut} 0.2s ease-in forwards`
      : css`${slideIn} 0.2s ease-out forwards`};
`;

const IconWrapper = styled.span`
  flex-shrink: 0;
  margin-top: 1px;
  color: ${({ type, theme }) => getBorderColor(type, theme)};
  line-height: 1;
`;

const Body = styled.div`
  flex: 1;
  min-width: 0;
`;

const Title = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text};
  line-height: 1.4;
`;

const Message = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textSecondary};
  margin-top: 2px;
  line-height: 1.4;
  word-break: break-word;
`;

const CloseBtn = styled.button`
  flex-shrink: 0;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: ${({ theme }) => theme.colors.textTertiary};
  display: flex;
  align-items: center;
  line-height: 1;
  margin-top: 1px;

  &:hover {
    color: ${({ theme }) => theme.colors.textSecondary};
  }
`;

const AUTO_DISMISS_MS = 5000;

function getTypeLabel(type) {
  if (type === 'warning') return 'Warning';
  if (type === 'error') return 'Error';
  return 'Info';
}

function WarningIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 3L2 17h16L10 3z" />
      <line x1="10" y1="9" x2="10" y2="13" />
      <circle cx="10" cy="15.5" r="0.5" fill="currentColor" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10" cy="10" r="8" />
      <line x1="10" y1="7" x2="10" y2="11" />
      <circle cx="10" cy="13.5" r="0.5" fill="currentColor" />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="10" cy="10" r="8" />
      <line x1="10" y1="9" x2="10" y2="14" />
      <circle cx="10" cy="6.5" r="0.5" fill="currentColor" />
    </svg>
  );
}

function getIcon(type) {
  if (type === 'warning') return <WarningIcon />;
  if (type === 'error') return <ErrorIcon />;
  return <InfoIcon />;
}

function CloseIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="5" y1="5" x2="15" y2="15" />
      <line x1="15" y1="5" x2="5" y2="15" />
    </svg>
  );
}

function ToastItem({ toast, onDismiss }) {
  const [exiting, setExiting] = useState(false);

  const dismiss = useCallback(() => {
    setExiting(true);
    setTimeout(() => onDismiss(toast.id), 200);
  }, [toast.id, onDismiss]);

  useEffect(() => {
    const timer = setTimeout(dismiss, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [dismiss]);

  return (
    <Item type={toast.type} exiting={exiting} onClick={dismiss}>
      <IconWrapper type={toast.type}>{getIcon(toast.type)}</IconWrapper>
      <Body>
        <Title>{toast.title || getTypeLabel(toast.type)}</Title>
        {toast.message && <Message>{toast.message}</Message>}
      </Body>
      <CloseBtn onClick={(e) => { e.stopPropagation(); dismiss(); }}>
        <CloseIcon />
      </CloseBtn>
    </Item>
  );
}

export function Toast({ toasts, onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <Container>
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </Container>
  );
}

export default Toast;
