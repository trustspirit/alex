import styled from 'styled-components';
import { useSettings } from '../../hooks/useSettings';
import ApiKeyForm from './ApiKeyForm';
import ModelSelector from './ModelSelector';

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

function SettingsPage() {
  const {
    providers,
    settings,
    loading,
    saving,
    saveApiKey,
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
    </PageWrapper>
  );
}

export default SettingsPage;
