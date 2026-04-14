import styled from 'styled-components';
import { NavLink } from 'react-router-dom';
import { useOnline } from '../hooks/useOnline';

const Wrapper = styled.div`
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
`;

const Sidebar = styled.nav`
  width: 56px;
  min-width: 56px;
  background: ${({ theme }) => theme.colors.surface};
  border-right: 1px solid ${({ theme }) => theme.colors.border};
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
  gap: 4px;
`;

const NavItem = styled(NavLink)`
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: ${({ theme }) => theme.radii.md};
  color: ${({ theme }) => theme.colors.textSecondary};
  transition: background 0.1s, color 0.1s;
  cursor: pointer;

  &:hover {
    background: ${({ theme }) => theme.colors.surfaceHover};
    color: ${({ theme }) => theme.colors.text};
  }

  &.active {
    background: ${({ theme }) => theme.colors.primary};
    color: #fff;
  }

  svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }
`;

const Main = styled.main`
  flex: 1;
  overflow: auto;
  background: ${({ theme }) => theme.colors.bg};
`;

const Spacer = styled.div`
  flex: 1;
`;

const OfflineBadge = styled.div`
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  color: #92400E;
  background: #FEF3C7;
  border-radius: 9999px;
  padding: 2px 8px;
  text-align: center;
`;

// SVG icons
const IconChat = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H6l-4 3V5z" />
  </svg>
);

const IconLearn = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="2" width="12" height="16" rx="1" />
    <line x1="7" y1="7" x2="13" y2="7" />
    <line x1="7" y1="10" x2="13" y2="10" />
    <line x1="7" y1="13" x2="10" y2="13" />
  </svg>
);

const IconSettings = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="10" cy="10" r="2.5" />
    <path d="M10 2v1.5M10 16.5V18M2 10h1.5M16.5 10H18M4.22 4.22l1.06 1.06M14.72 14.72l1.06 1.06M4.22 15.78l1.06-1.06M14.72 5.28l1.06-1.06" />
  </svg>
);

function Layout({ children }) {
  const isOnline = useOnline();

  return (
    <Wrapper>
      <Sidebar>
        <NavItem to="/chat" title="Chat">
          <IconChat />
        </NavItem>
        <NavItem to="/learn" title="Learn">
          <IconLearn />
        </NavItem>
        <NavItem to="/settings" title="Settings">
          <IconSettings />
        </NavItem>
        <Spacer />
        {!isOnline && <OfflineBadge>Offline</OfflineBadge>}
      </Sidebar>
      <Main>{children}</Main>
    </Wrapper>
  );
}

export default Layout;
