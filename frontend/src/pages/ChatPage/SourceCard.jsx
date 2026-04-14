import styled from 'styled-components';

const Card = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 10px;
  background: ${({ theme }) => theme.colors.bg};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  font-size: ${({ theme }) => theme.fontSizes.xs};
  line-height: 1.4;
`;

const SourceIcon = styled.div`
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${({ $hasWarning, theme }) =>
    $hasWarning ? theme.colors.warning : theme.colors.textTertiary};
  margin-top: 1px;
`;

const SourceBody = styled.div`
  flex: 1;
  min-width: 0;
`;

const SourceName = styled.div`
  color: ${({ theme }) => theme.colors.text};
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const SourceMeta = styled.div`
  color: ${({ theme }) => theme.colors.textTertiary};
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
`;

const WarningBadge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: ${({ theme }) => theme.colors.warning};
  font-size: 10px;
`;

const DocIcon = () => (
  <svg width="12" height="14" viewBox="0 0 12 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 1h6l2 2v10H2V1z" />
    <line x1="4" y1="5" x2="8" y2="5" />
    <line x1="4" y1="7.5" x2="8" y2="7.5" />
    <line x1="4" y1="10" x2="6" y2="10" />
  </svg>
);

const WarnIcon = () => (
  <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 1L9 9H1L5 1z" />
    <line x1="5" y1="4.5" x2="5" y2="6.5" />
    <circle cx="5" cy="7.8" r="0.3" fill="currentColor" />
  </svg>
);

function SourceCard({ source }) {
  const {
    document_name,
    document_title,
    page_number,
    score,
    has_warning,
    warning_reason,
  } = source;

  const displayName = document_title || document_name || 'Unknown source';
  const scoreDisplay = typeof score === 'number' ? `${(score * 100).toFixed(0)}%` : null;

  return (
    <Card>
      <SourceIcon $hasWarning={has_warning}>
        <DocIcon />
      </SourceIcon>
      <SourceBody>
        <SourceName title={displayName}>{displayName}</SourceName>
        <SourceMeta>
          {page_number != null && <span>p. {page_number}</span>}
          {scoreDisplay && <span>Relevance {scoreDisplay}</span>}
          {has_warning && (
            <WarningBadge title={warning_reason || 'Low confidence source'}>
              <WarnIcon />
              {warning_reason || 'Low confidence'}
            </WarningBadge>
          )}
        </SourceMeta>
      </SourceBody>
    </Card>
  );
}

export default SourceCard;
