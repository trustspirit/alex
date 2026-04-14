import { useState } from 'react';
import styled from 'styled-components';

const Card = styled.div`
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  overflow: hidden;
  font-size: ${({ theme }) => theme.fontSizes.xs};
`;

const FileHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: ${({ theme }) => theme.colors.bg};
  border-bottom: 1px solid ${({ theme }) => theme.colors.borderLight};
`;

const FileIcon = styled.span`
  color: ${({ $hasWarning, theme }) =>
    $hasWarning ? theme.colors.warning : theme.colors.textTertiary};
  display: flex;
  align-items: center;
`;

const FileName = styled.span`
  font-weight: 500;
  color: ${({ theme }) => theme.colors.text};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const WarningBadge = styled.span`
  color: ${({ theme }) => theme.colors.warning};
  font-size: 10px;
  display: flex;
  align-items: center;
  gap: 2px;
`;

const PageList = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0;
`;

const PageItem = styled.div`
  position: relative;
  padding: 6px 10px;
  cursor: default;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid ${({ theme }) => theme.colors.borderLight};
  transition: background 0.1s;
  width: 100%;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: ${({ theme }) => theme.colors.surfaceHover};
  }
`;

const PageLabel = styled.span`
  font-weight: 500;
  color: ${({ theme }) => theme.colors.primary};
  min-width: 40px;
`;

const ScoreText = styled.span`
  color: ${({ theme }) => theme.colors.textTertiary};
`;

const PreviewToggle = styled.span`
  color: ${({ theme }) => theme.colors.textTertiary};
  margin-left: auto;
  cursor: pointer;
  &:hover {
    color: ${({ theme }) => theme.colors.text};
  }
`;

const PreviewBox = styled.div`
  padding: 8px 10px;
  background: ${({ theme }) => theme.colors.bg};
  border-top: 1px solid ${({ theme }) => theme.colors.borderLight};
  font-size: 12px;
  line-height: 1.5;
  color: ${({ theme }) => theme.colors.textSecondary};
  white-space: pre-wrap;
  max-height: 150px;
  overflow-y: auto;
`;

const DocIcon = () => (
  <svg width="12" height="14" viewBox="0 0 12 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 1h6l2 2v10H2V1z" />
    <line x1="4" y1="5" x2="8" y2="5" />
    <line x1="4" y1="7.5" x2="8" y2="7.5" />
  </svg>
);

const WarnIcon = () => (
  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 1L9 9H1L5 1z" />
    <line x1="5" y1="4.5" x2="5" y2="6.5" />
  </svg>
);

function getDisplayName(source) {
  const path = source.source || '';
  if (source.type === 'youtube') return path;
  if (!path) return 'Unknown source';
  const parts = path.split('/');
  return parts[parts.length - 1] || path;
}

function SourceCard({ source }) {
  const [expandedPage, setExpandedPage] = useState(null);
  const displayName = getDisplayName(source);
  const hasWarning = Boolean(source.fallback);
  const pages = source.pages || [];

  return (
    <Card>
      <FileHeader>
        <FileIcon $hasWarning={hasWarning}>
          <DocIcon />
        </FileIcon>
        <FileName title={source.source}>{displayName}</FileName>
        {hasWarning && (
          <WarningBadge title="Parsed with fallback method">
            <WarnIcon /> Fallback
          </WarningBadge>
        )}
      </FileHeader>

      <PageList>
        {pages.map((p, idx) => {
          const scoreDisplay = typeof p.score === 'number' ? `${(p.score * 100).toFixed(0)}%` : null;
          const isExpanded = expandedPage === idx;

          return (
            <div key={idx}>
              <PageItem
                onClick={() => setExpandedPage(isExpanded ? null : idx)}
              >
                {p.page != null && <PageLabel>p. {p.page}</PageLabel>}
                {scoreDisplay && <ScoreText>Relevance {scoreDisplay}</ScoreText>}
                <PreviewToggle>{isExpanded ? '▲' : '▼'}</PreviewToggle>
              </PageItem>
              {isExpanded && p.preview && (
                <PreviewBox>{p.preview}</PreviewBox>
              )}
            </div>
          );
        })}
      </PageList>
    </Card>
  );
}

export default SourceCard;
