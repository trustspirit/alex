import { useState } from 'react';
import styled from 'styled-components';
import { useSync } from '../../hooks/useSync';
import { formatRelativeDate } from '../../utils/formatDate';

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const Description = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textSecondary};
  margin: 0;
`;

const FieldGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  @media (max-width: 600px) { grid-template-columns: 1fr; }
`;

const FieldGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const Label = styled.label`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textSecondary};
  font-weight: 500;
`;

const Input = styled.input`
  padding: 8px 10px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  background: ${({ theme }) => theme.colors.bg};
  color: ${({ theme }) => theme.colors.text};
  &:focus { outline: none; border-color: ${({ theme }) => theme.colors.primary}; }
`;

const Row = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const Button = styled.button`
  padding: 6px 14px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.text};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  cursor: pointer;
  &:hover { background: ${({ theme }) => theme.colors.bg}; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
`;

const StatusText = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ $success, theme }) => $success ? theme.colors.success : theme.colors.error};
`;

const ToggleRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Toggle = styled.button`
  width: 44px;
  height: 24px;
  border-radius: 12px;
  border: none;
  background: ${({ $on, theme }) => $on ? theme.colors.primary : theme.colors.border};
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
  &::after {
    content: '';
    position: absolute;
    top: 2px;
    left: ${({ $on }) => $on ? '22px' : '2px'};
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: white;
    transition: left 0.2s;
  }
`;

const SyncInfo = styled.div`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textTertiary};
`;

export default function SyncSettings({ settings, onSaveSetting, onSaveApiKey }) {
  const { syncStatus, lastSyncedAt, triggerSync, testConnection } = useSync();
  const [connectionResult, setConnectionResult] = useState(null);
  const [testing, setTesting] = useState(false);

  const [endpoint, setEndpoint] = useState(settings.r2_endpoint || '');
  const [bucket, setBucket] = useState(settings.r2_bucket || '');
  const [accessKey, setAccessKey] = useState('');
  const [secretKey, setSecretKey] = useState('');

  const enabled = settings.sync_enabled === 'true';
  const hasExistingKeys = settings.r2_access_key_id_api_key || settings.r2_access_key_id;
  const allFieldsFilled = endpoint && bucket && (accessKey || hasExistingKeys);

  const handleTestConnection = async () => {
    setTesting(true);
    if (endpoint) await onSaveSetting('r2_endpoint', endpoint);
    if (bucket) await onSaveSetting('r2_bucket', bucket);
    if (accessKey) await onSaveApiKey('r2_access_key_id', accessKey);
    if (secretKey) await onSaveApiKey('r2_secret_access_key', secretKey);
    const result = await testConnection();
    setConnectionResult(result);
    setTesting(false);
  };

  const handleToggle = async () => {
    await onSaveSetting('sync_enabled', enabled ? 'false' : 'true');
  };

  return (
    <Wrapper>
      <Description>Cloudflare R2를 통해 기기 간 지식베이스를 동기화합니다.</Description>
      <FieldGrid>
        <FieldGroup>
          <Label>R2 Endpoint</Label>
          <Input value={endpoint} onChange={(e) => setEndpoint(e.target.value)}
            onBlur={() => endpoint && onSaveSetting('r2_endpoint', endpoint)}
            placeholder="https://xxx.r2.cloudflarestorage.com" />
        </FieldGroup>
        <FieldGroup>
          <Label>Bucket Name</Label>
          <Input value={bucket} onChange={(e) => setBucket(e.target.value)}
            onBlur={() => bucket && onSaveSetting('r2_bucket', bucket)}
            placeholder="alex-sync" />
        </FieldGroup>
        <FieldGroup>
          <Label>Access Key</Label>
          <Input type="password" value={accessKey} onChange={(e) => setAccessKey(e.target.value)}
            placeholder={hasExistingKeys ? '(key saved)' : 'Access Key ID'} />
        </FieldGroup>
        <FieldGroup>
          <Label>Secret Key</Label>
          <Input type="password" value={secretKey} onChange={(e) => setSecretKey(e.target.value)}
            placeholder={hasExistingKeys ? '(key saved)' : 'Secret Access Key'} />
        </FieldGroup>
      </FieldGrid>
      <Row>
        <Button onClick={handleTestConnection} disabled={testing || !allFieldsFilled}>
          {testing ? 'Testing...' : 'Test Connection'}
        </Button>
        {connectionResult && (
          <StatusText $success={connectionResult.success}>
            {connectionResult.success ? '\u2713 Connected' : `\u2715 ${connectionResult.error || 'Failed'}`}
          </StatusText>
        )}
      </Row>
      <ToggleRow>
        <span>Sync</span>
        <Toggle $on={enabled} onClick={handleToggle} disabled={!allFieldsFilled} />
      </ToggleRow>
      {enabled && (
        <Row>
          <SyncInfo>
            {syncStatus === 'syncing' && '\uB3D9\uAE30\uD654 \uC911...'}
            {syncStatus === 'idle' && lastSyncedAt && `Last synced: ${formatRelativeDate(lastSyncedAt)}`}
            {syncStatus === 'error' && 'Sync error'}
          </SyncInfo>
          <Button onClick={triggerSync} disabled={syncStatus === 'syncing'}>Sync Now</Button>
        </Row>
      )}
    </Wrapper>
  );
}
