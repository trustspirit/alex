import styled from 'styled-components';
import { useLearn } from '../../hooks/useLearn';
import CollectionSidebar from './CollectionSidebar';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';

const PageWrapper = styled.div`
  display: flex;
  height: 100%;
  overflow: hidden;
  background: ${({ theme }) => theme.colors.bg};
`;

const MainArea = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const MainContent = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 32px 36px;
  display: flex;
  flex-direction: column;
  gap: 28px;
`;

const PageTitle = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes.xxl};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text};
  margin: 0 0 2px 0;
  letter-spacing: -0.02em;
`;

const PageSubtitle = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textSecondary};
  margin: 0 0 20px 0;
`;

const UploadSection = styled.section`
  background: ${({ theme }) => theme.colors.surface};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: 24px 28px;
  box-shadow: ${({ theme }) => theme.shadows.sm};
`;

const SectionTitle = styled.h2`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: ${({ theme }) => theme.colors.textTertiary};
  margin: 0 0 16px 0;
`;

function LearnPage() {
  const {
    documents,
    allDocuments,
    collections,
    selectedCollection,
    isUploading,
    progress,
    warnings,
    uploadFiles,
    uploadYoutube,
    deleteDocument,
    reindexDocument,
    selectCollection,
    createCollection,
    renameCollection,
    deleteCollection,
    refreshDocuments,
  } = useLearn();

  return (
    <PageWrapper>
      <CollectionSidebar
        collections={collections}
        selectedCollection={selectedCollection}
        allDocuments={allDocuments}
        onSelect={selectCollection}
        onCreate={createCollection}
        onRename={renameCollection}
        onDelete={deleteCollection}
      />

      <MainArea>
        <MainContent>
          <div>
            <PageTitle>Learn</PageTitle>
            <PageSubtitle>
              Upload documents or add YouTube videos to build your knowledge base.
            </PageSubtitle>
          </div>

          <UploadSection>
            <SectionTitle>Add Content</SectionTitle>
            <FileUpload
              onUploadFiles={uploadFiles}
              onUploadYoutube={uploadYoutube}
              isUploading={isUploading}
            />
          </UploadSection>

          <section>
            <SectionTitle style={{ marginBottom: 14 }}>
              {selectedCollection
                ? `${collections.find((c) => c.id === selectedCollection)?.name ?? 'Collection'}`
                : 'All Documents'}
            </SectionTitle>
            <DocumentList
              documents={documents}
              progress={progress}
              warnings={warnings}
              onDelete={deleteDocument}
              onReindex={reindexDocument}
              onTagsChanged={refreshDocuments}
            />
          </section>
        </MainContent>
      </MainArea>
    </PageWrapper>
  );
}

export default LearnPage;
