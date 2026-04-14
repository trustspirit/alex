import styled from 'styled-components';
import { useChat } from '../../hooks/useChat';
import ChatSidebar from './ChatSidebar';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

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
  position: relative;
`;

function ChatPage() {
  const {
    sessions,
    currentSessionId,
    messages,
    streamingText,
    isStreaming,
    queryError,
    loading,
    selectedCollectionId,
    collections,
    sendMessage,
    selectSession,
    createNewSession,
    deleteSession,
    setCollectionFilter,
  } = useChat();

  return (
    <PageWrapper>
      <ChatSidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        collections={collections}
        selectedCollectionId={selectedCollectionId}
        onSelectSession={selectSession}
        onNewSession={createNewSession}
        onDeleteSession={deleteSession}
        onCollectionFilter={setCollectionFilter}
      />

      <MainArea>
        <MessageList
          messages={messages}
          streamingText={streamingText}
          isStreaming={isStreaming}
          queryError={queryError}
          loading={loading}
        />
        <ChatInput
          onSend={sendMessage}
          disabled={isStreaming || loading}
        />
      </MainArea>
    </PageWrapper>
  );
}

export default ChatPage;
