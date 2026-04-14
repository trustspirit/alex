import { useState, useCallback } from 'react';
import styled, { keyframes, css } from 'styled-components';

const progressAnim = keyframes`
  from { opacity: 0.6; }
  to { opacity: 1; }
`;

const Card = styled.div`
  background: ${({ theme }) => theme.colors.surface};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: 16px;
  position: relative;
  transition: box-shadow 0.15s;

  &:hover {
    box-shadow: ${({ theme }) => theme.shadows.md};
  }

  &:hover [data-delete],
  &:hover [data-reindex] {
    opacity: 1;
  }
`;

const CardTop = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
`;

const TitleRow = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
`;

const Title = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.md};
  font-weight: 500;
  color: ${({ theme }) => theme.colors.text};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const SourceBadge = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  flex-shrink: 0;
  color: ${({ $type, theme }) => {
    switch ($type) {
      case 'pdf': return '#DC2626';
      case 'md': return '#7C3AED';
      case 'txt': return '#059669';
      case 'youtube': return '#DC2626';
      default: return theme.colors.textSecondary;
    }
  }};
`;

const ActionButton = styled.button`
  opacity: 0;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  color: ${({ theme }) => theme.colors.textTertiary};
  border-radius: ${({ theme }) => theme.radii.sm};
  transition: opacity 0.15s, color 0.15s, background 0.15s;
  flex-shrink: 0;

  &:hover {
    color: ${({ $variant, theme }) => $variant === 'danger' ? theme.colors.error : theme.colors.primary};
    background: ${({ $variant, theme }) => $variant === 'danger' ? theme.colors.errorBg : 'rgba(59,130,246,0.08)'};
  }
`;

const DeleteButton = styled(ActionButton).attrs({ $variant: 'danger' })``;
const ReindexButton = styled(ActionButton).attrs({ $variant: 'primary' })``;

const CardMeta = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
`;

const StatusText = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-weight: 500;
  color: ${({ $status, theme }) => {
    switch ($status) {
      case 'pending': return theme.colors.textTertiary;
      case 'processing': return theme.colors.primary;
      case 'completed': return theme.colors.success;
      case 'failed': return theme.colors.error;
      default: return theme.colors.textTertiary;
    }
  }};
`;

const DateText = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textTertiary};
`;

const ProgressTrack = styled.div`
  height: 4px;
  background: ${({ theme }) => theme.colors.borderLight};
  border-radius: 2px;
  margin-top: 10px;
  overflow: hidden;
`;

const ProgressFill = styled.div`
  height: 100%;
  background: ${({ theme }) => theme.colors.primary};
  border-radius: 2px;
  width: ${({ $pct }) => $pct}%;
  transition: width 0.3s ease;
  animation: ${progressAnim} 1s ease-in-out infinite alternate;
`;

const WarningIcon = styled.span`
  display: inline-flex;
  align-items: center;
  cursor: default;
  position: relative;

  &:hover [data-tooltip] {
    display: block;
  }
`;

const Tooltip = styled.span`
  display: none;
  position: absolute;
  bottom: calc(100% + 4px);
  left: 50%;
  transform: translateX(-50%);
  background: ${({ theme }) => theme.colors.text};
  color: #fff;
  font-size: ${({ theme }) => theme.fontSizes.xs};
  padding: 4px 8px;
  border-radius: ${({ theme }) => theme.radii.sm};
  white-space: nowrap;
  max-width: 220px;
  white-space: normal;
  text-align: center;
  z-index: 10;
  pointer-events: none;
`;

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="2 4 14 4" />
    <path d="M5 4V2h6v2" />
    <path d="M3 4l1 10h8l1-10" />
    <line x1="6" y1="7" x2="6" y2="11" />
    <line x1="10" y1="7" x2="10" y2="11" />
  </svg>
);

const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 2v5h5" />
    <path d="M15 14v-5h-5" />
    <path d="M2.3 10a6 6 0 0 0 10.3 1.4l2.4-2.4" />
    <path d="M13.7 6A6 6 0 0 0 3.4 4.6L1 7" />
  </svg>
);

const WarnTriangle = () => (
  <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="#D97706" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M8 2L14 13H2L8 2z" />
    <line x1="8" y1="7" x2="8" y2="9.5" />
    <circle cx="8" cy="11.5" r="0.5" fill="#D97706" stroke="none" />
  </svg>
);

function formatRelativeDate(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  if (diffSec < 60) return 'just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}

function DocumentCard({ doc, docProgress, docWarnings, onDelete, onReindex }) {
  const status = doc.status || 'pending';
  const pct = docProgress?.percent ?? 0;
  const hasWarning = doc.fallback_used || (docWarnings && docWarnings.length > 0);
  const warningMessage =
    docWarnings?.[0]?.warning ||
    (doc.fallback_used ? 'Fallback used during processing' : '');

  return (
    <Card>
      <CardTop>
        <TitleRow>
          <Title title={doc.title || doc.filename || 'Untitled'}>
            {doc.title || doc.filename || 'Untitled'}
          </Title>
          {hasWarning && (
            <WarningIcon title={warningMessage}>
              <WarnTriangle />
              {warningMessage && (
                <Tooltip data-tooltip>{warningMessage}</Tooltip>
              )}
            </WarningIcon>
          )}
        </TitleRow>
        {onReindex && (
          <ReindexButton
            data-reindex
            title="Re-index document"
            onClick={() => onReindex(doc.id)}
          >
            <RefreshIcon />
          </ReindexButton>
        )}
        <DeleteButton
          data-delete
          title="Delete document"
          onClick={() => onDelete(doc.id)}
        >
          <TrashIcon />
        </DeleteButton>
      </CardTop>

      <CardMeta>
        <SourceBadge $type={doc.source_type}>{doc.source_type || '—'}</SourceBadge>
        <StatusText $status={status}>{status}</StatusText>
        {doc.created_at && (
          <DateText>{formatRelativeDate(doc.created_at)}</DateText>
        )}
      </CardMeta>

      {status === 'processing' && (
        <ProgressTrack>
          <ProgressFill $pct={pct} />
        </ProgressTrack>
      )}
    </Card>
  );
}

export default DocumentCard;
