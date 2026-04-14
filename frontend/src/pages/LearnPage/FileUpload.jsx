import { useState, useRef, useCallback } from 'react';
import styled, { keyframes } from 'styled-components';

const spin = keyframes`
  to { transform: rotate(360deg); }
`;

const DropZone = styled.div`
  border: 2px dashed ${({ theme, $isDragging }) =>
    $isDragging ? theme.colors.primary : theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: 36px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  background: ${({ theme, $isDragging }) =>
    $isDragging ? `${theme.colors.primary}08` : theme.colors.surface};

  &:hover {
    border-color: ${({ theme }) => theme.colors.primary};
    background: ${({ theme }) => `${theme.colors.primary}08`};
  }
`;

const DropText = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.md};
  color: ${({ theme }) => theme.colors.textSecondary};
  margin: 0;
  text-align: center;
`;

const DropSubText = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textTertiary};
  margin: 0;
  text-align: center;
`;

const HiddenInput = styled.input`
  display: none;
`;

const Divider = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0 0;
  color: ${({ theme }) => theme.colors.textTertiary};
  font-size: ${({ theme }) => theme.fontSizes.xs};

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: ${({ theme }) => theme.colors.border};
  }
`;

const YoutubeRow = styled.div`
  display: flex;
  gap: 8px;
  margin-top: 12px;
`;

const UrlInput = styled.input`
  flex: 1;
  padding: 8px 12px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.text};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  outline: none;
  transition: border-color 0.15s;

  &:focus {
    border-color: ${({ theme }) => theme.colors.primary};
  }

  &::placeholder {
    color: ${({ theme }) => theme.colors.textTertiary};
  }
`;

const AddButton = styled.button`
  padding: 8px 16px;
  background: ${({ theme }) => theme.colors.primary};
  color: #fff;
  border: none;
  border-radius: ${({ theme }) => theme.radii.md};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;

  &:hover:not(:disabled) {
    background: ${({ theme }) => theme.colors.primaryHover};
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const UploadingRow = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.primary};
`;

const Spinner = styled.div`
  width: 14px;
  height: 14px;
  border: 2px solid ${({ theme }) => `${theme.colors.primary}33`};
  border-top-color: ${({ theme }) => theme.colors.primary};
  border-radius: 50%;
  animation: ${spin} 0.7s linear infinite;
`;

const UploadIcon = () => (
  <svg
    width="32"
    height="32"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={{ color: '#999', marginBottom: 4 }}
  >
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

function FileUpload({ onUploadFiles, onUploadYoutube, isUploading }) {
  const [isDragging, setIsDragging] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState('');

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      // PyWebView drag & drop does NOT provide file paths (only filenames).
      // Trigger native file dialog instead so we get full paths from the OS.
      onUploadFiles(null);
    },
    [onUploadFiles]
  );

  // Click also opens native OS file dialog via Python bridge
  const handleClick = useCallback(() => {
    onUploadFiles(null);
  }, [onUploadFiles]);

  const handleYoutubeSubmit = useCallback(
    (e) => {
      e.preventDefault();
      const trimmed = youtubeUrl.trim();
      if (!trimmed) return;
      onUploadYoutube(trimmed);
      setYoutubeUrl('');
    },
    [youtubeUrl, onUploadYoutube]
  );

  return (
    <div>
      <DropZone
        $isDragging={isDragging}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <UploadIcon />
        <DropText>Drop files here or click to select</DropText>
        <DropSubText>PDF, Markdown, and plain text files</DropSubText>
      </DropZone>

      <Divider>or</Divider>

      <YoutubeRow as="form" onSubmit={handleYoutubeSubmit}>
        <UrlInput
          type="url"
          placeholder="Paste a YouTube URL…"
          value={youtubeUrl}
          onChange={(e) => setYoutubeUrl(e.target.value)}
          disabled={isUploading}
        />
        <AddButton type="submit" disabled={isUploading || !youtubeUrl.trim()}>
          Add
        </AddButton>
      </YoutubeRow>

      {isUploading && (
        <UploadingRow>
          <Spinner />
          Uploading…
        </UploadingRow>
      )}
    </div>
  );
}

export default FileUpload;
