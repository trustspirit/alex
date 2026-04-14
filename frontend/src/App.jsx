import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import styled, { keyframes } from 'styled-components';
import theme from './styles/theme';
import GlobalStyle from './styles/GlobalStyle';
import Layout from './components/Layout';
import SettingsPage from './pages/SettingsPage';
import LearnPage from './pages/LearnPage';
import ChatPage from './pages/ChatPage';
import SearchModal from './components/SearchModal';

const fadeIn = keyframes`
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
`;

const PageWrapper = styled.div`
  animation: ${fadeIn} 0.15s ease-out;
  height: 100%;
`;

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <PageWrapper key={location.pathname}>
      <Routes location={location}>
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/learn" element={<LearnPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </PageWrapper>
  );
}

function App() {
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
      if (e.key === 'Escape') setSearchOpen(false);
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <BrowserRouter>
        <Layout>
          <AnimatedRoutes />
        </Layout>
        {searchOpen && (
          <SearchModal onClose={() => setSearchOpen(false)} />
        )}
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
