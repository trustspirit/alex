import styled, { keyframes } from 'styled-components';

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const Spinner = styled.span`
  display: inline-block;
  width: ${({ size }) => size || 20}px;
  height: ${({ size }) => size || 20}px;
  border-radius: 50%;
  border: 2px solid ${({ theme }) => theme.colors.border};
  border-top-color: ${({ theme }) => theme.colors.primary};
  animation: ${spin} 0.7s linear infinite;
  flex-shrink: 0;
`;

function LoadingSpinner({ size, className }) {
  return <Spinner size={size} className={className} />;
}

export default LoadingSpinner;
