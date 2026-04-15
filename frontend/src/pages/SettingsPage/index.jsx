import styled from 'styled-components';
import { useSettings } from '../../hooks/useSettings';
import ApiKeyForm from './ApiKeyForm';
import ModelSelector from './ModelSelector';
import SyncSettings from './SyncSettings';

const PageWrapper = styled.div`
  min-height: 100%;
  padding: 40px 48px;
  background: ${({ theme }) => theme.colors.bg};
`;

const PageTitle = styled.h1`
  font-size: ${({ theme }) => theme.fontSizes.xxl};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text};
  margin: 0 0 32px 0;
  letter-spacing: -0.02em;
`;

const Section = styled.section`
  background: ${({ theme }) => theme.colors.surface};
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.lg};
  padding: 28px 32px;
  margin-bottom: 24px;
  box-shadow: ${({ theme }) => theme.shadows.sm};
`;

const SectionHeader = styled.div`
  margin-bottom: 24px;
`;

const SectionTitle = styled.h2`
  font-size: ${({ theme }) => theme.fontSizes.lg};
  font-weight: 600;
  color: ${({ theme }) => theme.colors.text};
  margin: 0 0 4px 0;
`;

const SectionDesc = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textSecondary};
  margin: 0;
`;

const Divider = styled.hr`
  border: none;
  border-top: 1px solid ${({ theme }) => theme.colors.borderLight};
  margin: 20px 0;
`;

const ProviderList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const LoadingText = styled.p`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  color: ${({ theme }) => theme.colors.textSecondary};
  margin: 0;
`;

const SystemPromptArea = styled.textarea`
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.text};
  font-family: ${({ theme }) => theme.fonts.mono};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  line-height: 1.6;
  resize: vertical;
  outline: none;

  &:focus {
    border-color: ${({ theme }) => theme.colors.primary};
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  }

  &::placeholder {
    color: ${({ theme }) => theme.colors.textTertiary};
  }
`;

const SavedIndicator = styled.span`
  display: inline-block;
  margin-top: 8px;
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.success};
`;

function SettingsPage() {
  const {
    providers,
    settings,
    loading,
    saving,
    saveApiKey,
    saveSetting,
    selectDefaultProvider,
    selectDefaultModel,
    selectEmbedModel,
  } = useSettings();

  return (
    <PageWrapper>
      <PageTitle>Settings</PageTitle>

      <Section>
        <SectionHeader>
          <SectionTitle>API Keys</SectionTitle>
          <SectionDesc>
            Enter your API keys for each provider. Keys are stored securely in the system keychain.
          </SectionDesc>
        </SectionHeader>

        {loading ? (
          <LoadingText>Loading providers…</LoadingText>
        ) : (
          <ProviderList>
            {providers.map((provider, index) => (
              <div key={provider.name}>
                {index > 0 && <Divider />}
                <ApiKeyForm
                  provider={provider}
                  savingStatus={saving[`apiKey_${provider.name}`]}
                  onSave={saveApiKey}
                  hasExistingKey={settings[`${provider.name}_api_key`] === '__secret__'}
                />
              </div>
            ))}
            <Divider />
            <ApiKeyForm
              provider={{ name: 'llamaparse', display_name: 'LlamaParse (PDF parsing)' }}
              savingStatus={saving['apiKey_llamaparse']}
              onSave={saveApiKey}
              hasExistingKey={settings['llamaparse_api_key'] === '__secret__'}
            />
          </ProviderList>
        )}
      </Section>

      <Section>
        <SectionHeader>
          <SectionTitle>Models</SectionTitle>
          <SectionDesc>
            Choose the default LLM provider, chat model, and embedding model for document indexing.
          </SectionDesc>
        </SectionHeader>

        {loading ? (
          <LoadingText>Loading models…</LoadingText>
        ) : (
          <ModelSelector
            providers={providers}
            settings={settings}
            saving={saving}
            onSelectProvider={selectDefaultProvider}
            onSelectModel={selectDefaultModel}
            onSelectEmbedModel={selectEmbedModel}
          />
        )}
      </Section>

      <Section>
        <SectionHeader>
          <SectionTitle>System Prompt</SectionTitle>
          <SectionDesc>
            Customize how the AI responds to your questions. This prompt is sent with every query.
          </SectionDesc>
        </SectionHeader>

        <SystemPromptArea
          value={settings.system_prompt || ''}
          onChange={(e) => saveSetting('system_prompt', e.target.value)}
          placeholder={`Example:\n- Answer in Korean\n- Provide detailed explanations\n- Include page references when possible`}
          rows={6}
        />
        {saving.system_prompt === 'saved' && (
          <SavedIndicator>Saved</SavedIndicator>
        )}
      </Section>

      <Section>
        <SectionTitle>Cloud Sync</SectionTitle>
        <SyncSettings settings={settings} onSaveSetting={saveSetting} onSaveApiKey={saveApiKey} />
      </Section>
    </PageWrapper>
  );
}

export default SettingsPage;
