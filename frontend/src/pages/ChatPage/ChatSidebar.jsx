import { useCallback } from 'react';
import styled from 'styled-components';
import { formatRelativeDate } from '../../utils/formatDate';

const Sidebar = styled.aside`
  width: 280px;
  min-width: 280px;
  background: ${({ theme }) => theme.colors.surface};
  border-right: 1px solid ${({ theme }) => theme.colors.border};
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const SidebarTop = styled.div`
  padding: 16px 12px 12px;
`;

const NewChatBtn = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  background: ${({ theme }) => theme.colors.primary};
  color: #fff;
  border: none;
  border-radius: ${({ theme }) => theme.radii.md};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
  cursor: pointer;
  transition: background 0.1s;

  &:hover {
    background: ${({ theme }) => theme.colors.primaryHover};
  }

  svg {
    flex-shrink: 0;
  }
`;

const ShortcutHint = styled.span`
  margin-left: auto;
  font-size: ${({ theme }) => theme.fontSizes.xs};
  opacity: 0.7;
  font-weight: 400;
`;

const FilterSection = styled.div`
  padding: 0 12px 12px;
`;

const FilterLabel = styled.label`
  display: block;
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: ${({ theme }) => theme.colors.textTertiary};
  margin-bottom: 6px;
`;

const FilterSelect = styled.select`
  width: 100%;
  padding: 7px 10px;
  background: ${({ theme }) => theme.colors.bg};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.text};
  cursor: pointer;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%23999' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 28px;

  &:focus {
    border-color: ${({ theme }) => theme.colors.primary};
  }
`;

const Divider = styled.div`
  height: 1px;
  background: ${({ theme }) => theme.colors.borderLight};
  margin: 0 0 4px;
`;

const SectionLabel = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: ${({ theme }) => theme.colors.textTertiary};
  padding: 8px 16px 4px;
`;

const SessionList = styled.ul`
  list-style: none;
  padding: 4px 0 8px;
  margin: 0;
  flex: 1;
  overflow-y: auto;
`;

const SessionItem = styled.li`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin: 1px 6px;
  border-radius: ${({ theme }) => theme.radii.md};
  cursor: pointer;
  background: ${({ $selected, theme }) =>
    $selected ? `${theme.colors.primary}10` : 'transparent'};
  border-left: 2px solid ${({ $selected, theme }) =>
    $selected ? theme.colors.primary : 'transparent'};
  transition: background 0.1s, border-color 0.1s;

  &:hover {
    background: ${({ $selected, theme }) =>
      $selected ? `${theme.colors.primary}14` : theme.colors.surfaceHover};
  }

  &:hover [data-action] {
    opacity: 1;
  }
`;

const SessionInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const SessionTitle = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: ${({ $selected }) => ($selected ? '500' : '400')};
  color: ${({ $selected, theme }) =>
    $selected ? theme.colors.primary : theme.colors.text};
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
`;

const SessionTime = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textTertiary};
  margin-top: 2px;
`;

const DeleteBtn = styled.button`
  opacity: 0;
  flex-shrink: 0;
  background: none;
  border: none;
  padding: 3px 4px;
  cursor: pointer;
  color: ${({ theme }) => theme.colors.textTertiary};
  border-radius: ${({ theme }) => theme.radii.sm};
  display: flex;
  align-items: center;
  transition: opacity 0.15s, color 0.15s, background 0.15s;
  margin-left: 6px;

  &:hover {
    color: ${({ theme }) => theme.colors.error};
    background: ${({ theme }) => theme.colors.errorBg};
  }
`;

const EmptyState = styled.div`
  padding: 20px 16px;
  text-align: center;
  color: ${({ theme }) => theme.colors.textTertiary};
  font-size: ${({ theme }) => theme.fontSizes.sm};
`;

const PlusIcon = () => (
  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="7" y1="1" x2="7" y2="13" />
    <line x1="1" y1="7" x2="13" y2="7" />
  </svg>
);

const TrashIcon = () => (
  <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="1 3 13 3" />
    <path d="M4 3V1.5h6V3" />
    <path d="M2.5 3l.9 9h7.2l.9-9" />
  </svg>
);

function ChatSidebar({
  sessions,
  currentSessionId,
  collections,
  selectedCollectionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onCollectionFilter,
}) {
  const handleCollectionChange = useCallback(
    (e) => {
      const val = e.target.value;
      onCollectionFilter(val === '' ? null : parseInt(val, 10));
    },
    [onCollectionFilter]
  );

  return (
    <Sidebar>
      <SidebarTop>
        <NewChatBtn onClick={onNewSession}>
          <PlusIcon />
          New Chat
          <ShortcutHint>⌘N</ShortcutHint>
        </NewChatBtn>
      </SidebarTop>

      <FilterSection>
        <FilterLabel htmlFor="collection-filter">Search in</FilterLabel>
        <FilterSelect
          id="collection-filter"
          value={selectedCollectionId ?? ''}
          onChange={handleCollectionChange}
        >
          <option value="">All collections</option>
          {collections.map((col) => (
            <option key={col.id} value={col.id}>
              {col.name}
            </option>
          ))}
        </FilterSelect>
      </FilterSection>

      <Divider />

      <SectionLabel>Chats</SectionLabel>

      <SessionList>
        {sessions.length === 0 ? (
          <EmptyState>No chats yet</EmptyState>
        ) : (
          sessions.map((session) => {
            const selected = session.id === currentSessionId;
            return (
              <SessionItem
                key={session.id}
                $selected={selected}
                onClick={() => onSelectSession(session.id)}
              >
                <SessionInfo>
                  <SessionTitle $selected={selected}>
                    {session.title || 'Untitled Chat'}
                  </SessionTitle>
                  <SessionTime>
                    {formatRelativeDate(session.updated_at || session.created_at)}
                  </SessionTime>
                </SessionInfo>
                <DeleteBtn
                  data-action
                  title="Delete chat"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(session.id);
                  }}
                >
                  <TrashIcon />
                </DeleteBtn>
              </SessionItem>
            );
          })
        )}
      </SessionList>
    </Sidebar>
  );
}

export default ChatSidebar;
