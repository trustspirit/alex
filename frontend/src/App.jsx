import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import theme from './styles/theme';
import GlobalStyle from './styles/GlobalStyle';
import Layout from './components/Layout';

// Temporary placeholder pages
const ChatPage = () => <div style={{ padding: '24px' }}>Chat Page — coming soon</div>;
const LearnPage = () => <div style={{ padding: '24px' }}>Learn Page — coming soon</div>;
const SettingsPage = () => <div style={{ padding: '24px' }}>Settings Page — coming soon</div>;

function App() {
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/learn" element={<LearnPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/chat" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
