import { createGlobalStyle } from 'styled-components';

const GlobalStyle = createGlobalStyle`
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: ${({ theme }) => theme.fonts.body};
    font-size: ${({ theme }) => theme.fontSizes.md};
    color: ${({ theme }) => theme.colors.text};
    background: ${({ theme }) => theme.colors.bg};
    -webkit-font-smoothing: antialiased;
    line-height: 1.5;
  }
  input, textarea, button, select { font-family: inherit; font-size: inherit; }
  a { color: ${({ theme }) => theme.colors.primary}; text-decoration: none; }
  ::selection { background: ${({ theme }) => theme.colors.primary}; color: white; }
`;
export default GlobalStyle;
