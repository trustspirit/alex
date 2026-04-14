import styled from 'styled-components';
import DocumentCard from './DocumentCard';

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
`;

const EmptyState = styled.div`
  padding: 48px 24px;
  text-align: center;
  color: ${({ theme }) => theme.colors.textTertiary};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  border: 1px dashed ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.lg};
  background: ${({ theme }) => theme.colors.surface};
`;

function DocumentList({ documents, progress, warnings, onDelete, onReindex }) {
  if (!documents || documents.length === 0) {
    return (
      <EmptyState>
        No documents yet. Upload files or add YouTube links to get started.
      </EmptyState>
    );
  }

  return (
    <Grid>
      {documents.map((doc) => {
        const docProgress = progress?.[doc.id];
        const docWarnings = warnings?.filter((w) => w.doc_id === doc.id);
        return (
          <DocumentCard
            key={doc.id}
            doc={doc}
            docProgress={docProgress}
            docWarnings={docWarnings}
            onDelete={onDelete}
            onReindex={onReindex}
          />
        );
      })}
    </Grid>
  );
}

export default DocumentList;
