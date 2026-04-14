import { useState } from 'react';
import styled from 'styled-components';

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
  color: ${({ theme }) => theme.colors.text};
`;

const InputRow = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
`;

const Input = styled.input`
  flex: 1;
  height: 36px;
  padding: 0 12px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.text};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  outline: none;
  transition: border-color 0.15s;

  &:focus {
    border-color: ${({ theme }) => theme.colors.primary};
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  }

  &::placeholder {
    color: ${({ theme }) => theme.colors.textTertiary};
  }
`;

const IconButton = styled.button`
  height: 36px;
  width: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.textSecondary};
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.1s, color 0.1s, border-color 0.1s;

  &:hover {
    background: ${({ theme }) => theme.colors.surfaceHover};
    color: ${({ theme }) => theme.colors.text};
    border-color: #d0d0d0;
  }

  svg {
    width: 15px;
    height: 15px;
  }
`;

const SaveButton = styled.button`
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ $saved, theme }) =>
    $saved ? theme.colors.success : theme.colors.primary};
  color: #fff;
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
  cursor: ${({ disabled }) => (disabled ? 'default' : 'pointer')};
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: background 0.15s;

  &:hover:not(:disabled) {
    background: ${({ $saved, theme }) =>
      $saved ? theme.colors.success : theme.colors.primaryHover};
  }

  &:disabled {
    opacity: 0.6;
  }
`;

const ErrorText = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.error};
`;

const IconEyeOpen = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 10s3-5 8-5 8 5 8 5-3 5-8 5-8-5-8-5z" />
    <circle cx="10" cy="10" r="2" />
  </svg>
);

const IconEyeClosed = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 3l14 14M12.45 12.45A3.5 3.5 0 017.55 7.55M9 4.07A8 8 0 0118 10s-1.26 2.1-3.23 3.5M3.5 6.5C2.39 7.66 2 10 2 10s3 5 8 5c1.38 0 2.65-.32 3.77-.87" />
  </svg>
);

const IconCheck = () => (
  <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 10l4 4 8-8" />
  </svg>
);

function ApiKeyForm({ provider, savingStatus, onSave }) {
  const [value, setValue] = useState('');
  const [visible, setVisible] = useState(false);
  const [touched, setTouched] = useState(false);

  const isEmpty = value.trim() === '';
  const showError = touched && isEmpty;
  const isSaved = savingStatus === 'saved';
  const isSaving = savingStatus === 'saving';

  function handleSubmit(e) {
    e.preventDefault();
    setTouched(true);
    if (!isEmpty) {
      onSave(provider.name, value.trim());
    }
  }

  return (
    <Wrapper>
      <Label htmlFor={`apikey-${provider.name}`}>
        {provider.display_name}
      </Label>
      <form onSubmit={handleSubmit} noValidate>
        <InputRow>
          <Input
            id={`apikey-${provider.name}`}
            type={visible ? 'text' : 'password'}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onBlur={() => setTouched(true)}
            placeholder={`Enter ${provider.display_name} API key`}
            autoComplete="off"
            spellCheck={false}
          />
          <IconButton
            type="button"
            title={visible ? 'Hide key' : 'Show key'}
            onClick={() => setVisible((v) => !v)}
          >
            {visible ? <IconEyeClosed /> : <IconEyeOpen />}
          </IconButton>
          <SaveButton
            type="submit"
            $saved={isSaved}
            disabled={isSaving}
          >
            {isSaved && <IconCheck />}
            {isSaved ? 'Saved' : isSaving ? 'Saving…' : 'Save'}
          </SaveButton>
        </InputRow>
      </form>
      {showError && <ErrorText>API key cannot be empty.</ErrorText>}
    </Wrapper>
  );
}

export default ApiKeyForm;
