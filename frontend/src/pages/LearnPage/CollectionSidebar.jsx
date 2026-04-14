import { useState, useRef, useCallback } from 'react';
import styled from 'styled-components';

const Sidebar = styled.aside`
  width: 240px;
  min-width: 240px;
  background: ${({ theme }) => theme.colors.surface};
  border-right: 1px solid ${({ theme }) => theme.colors.border};
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const SidebarHeader = styled.div`
  padding: 20px 16px 12px;
  border-bottom: 1px solid ${({ theme }) => theme.colors.borderLight};
`;

const SidebarTitle = styled.h2`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: ${({ theme }) => theme.colors.textTertiary};
  margin: 0;
`;

const CollectionList = styled.ul`
  list-style: none;
  padding: 8px 0;
  margin: 0;
  flex: 1;
  overflow-y: auto;
`;

const CollectionItem = styled.li`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 12px;
  cursor: pointer;
  border-radius: ${({ theme }) => theme.radii.md};
  margin: 1px 6px;
  background: ${({ $selected, theme }) =>
    $selected ? `${theme.colors.primary}12` : 'transparent'};
  color: ${({ $selected, theme }) =>
    $selected ? theme.colors.primary : theme.colors.text};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: ${({ $selected }) => ($selected ? '500' : '400')};
  transition: background 0.1s, color 0.1s;

  &:hover {
    background: ${({ $selected, theme }) =>
      $selected ? `${theme.colors.primary}18` : theme.colors.surfaceHover};
  }

  &:hover [data-action] {
    opacity: 1;
  }
`;

const CollectionLabel = styled.span`
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const CollectionCount = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textTertiary};
  margin-left: 4px;
  flex-shrink: 0;
`;

const ActionButton = styled.button`
  opacity: 0;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 3px;
  color: ${({ theme }) => theme.colors.textTertiary};
  border-radius: ${({ theme }) => theme.radii.sm};
  display: flex;
  align-items: center;
  transition: opacity 0.15s, color 0.15s, background 0.15s;
  flex-shrink: 0;

  &:hover {
    color: ${({ theme }) => theme.colors.error};
    background: ${({ theme }) => theme.colors.errorBg};
  }
`;

const RenameInput = styled.input`
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.text};
  padding: 0;
`;

const Footer = styled.div`
  padding: 8px;
  border-top: 1px solid ${({ theme }) => theme.colors.borderLight};
`;

const NewCollectionBtn = styled.button`
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: 1px dashed ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  color: ${({ theme }) => theme.colors.textSecondary};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, color 0.15s, background 0.15s;

  &:hover {
    border-color: ${({ theme }) => theme.colors.primary};
    color: ${({ theme }) => theme.colors.primary};
    background: ${({ theme }) => `${theme.colors.primary}06`};
  }
`;

const TrashIcon = () => (
  <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="2 4 14 4" />
    <path d="M5 4V2h6v2" />
    <path d="M3 4l1 10h8l1-10" />
  </svg>
);

const PlusIcon = () => (
  <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="8" y1="2" x2="8" y2="14" />
    <line x1="2" y1="8" x2="14" y2="8" />
  </svg>
);

function CollectionSidebar({
  collections,
  selectedCollection,
  allDocuments,
  onSelect,
  onCreate,
  onRename,
  onDelete,
}) {
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const renameRef = useRef(null);

  const startRename = useCallback((col, e) => {
    e.stopPropagation();
    setRenamingId(col.id);
    setRenameValue(col.name);
    setTimeout(() => renameRef.current?.focus(), 0);
  }, []);

  const commitRename = useCallback(
    (id) => {
      const trimmed = renameValue.trim();
      if (trimmed) onRename(id, trimmed);
      setRenamingId(null);
    },
    [renameValue, onRename]
  );

  const handleRenameKey = useCallback(
    (e, id) => {
      if (e.key === 'Enter') commitRename(id);
      if (e.key === 'Escape') setRenamingId(null);
    },
    [commitRename]
  );

  const docCountFor = useCallback(
    (colId) => allDocuments?.filter((d) => d.collection_id === colId).length ?? 0,
    [allDocuments]
  );

  const allCount = allDocuments?.length ?? 0;

  return (
    <Sidebar>
      <SidebarHeader>
        <SidebarTitle>Collections</SidebarTitle>
      </SidebarHeader>

      <CollectionList>
        {/* "All Documents" option */}
        <CollectionItem
          $selected={selectedCollection === null}
          onClick={() => onSelect(null)}
        >
          <CollectionLabel>All Documents</CollectionLabel>
          <CollectionCount>{allCount}</CollectionCount>
        </CollectionItem>

        {collections.map((col) => (
          <CollectionItem
            key={col.id}
            $selected={selectedCollection === col.id}
            onClick={() => onSelect(col.id)}
            onDoubleClick={(e) => startRename(col, e)}
          >
            {renamingId === col.id ? (
              <RenameInput
                ref={renameRef}
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={() => commitRename(col.id)}
                onKeyDown={(e) => handleRenameKey(e, col.id)}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <>
                <CollectionLabel>{col.name}</CollectionLabel>
                <CollectionCount>{docCountFor(col.id)}</CollectionCount>
              </>
            )}
            <ActionButton
              data-action
              title="Delete collection"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(col.id);
              }}
            >
              <TrashIcon />
            </ActionButton>
          </CollectionItem>
        ))}
      </CollectionList>

      <Footer>
        <NewCollectionBtn onClick={() => onCreate('New Collection')}>
          <PlusIcon /> New Collection
        </NewCollectionBtn>
      </Footer>
    </Sidebar>
  );
}

export default CollectionSidebar;
