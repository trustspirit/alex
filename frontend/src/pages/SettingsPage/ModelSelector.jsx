import styled from 'styled-components';

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
`;

const Field = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: ${({ theme }) => theme.fontSizes.sm};
  font-weight: 500;
  color: ${({ theme }) => theme.colors.text};
`;

const SubLabel = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.textSecondary};
  margin-top: -4px;
`;

const Select = styled.select`
  height: 36px;
  padding: 0 32px 0 12px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme }) => theme.colors.text};
  font-size: ${({ theme }) => theme.fontSizes.sm};
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236B6B6B' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  transition: border-color 0.15s;

  &:focus {
    border-color: ${({ theme }) => theme.colors.primary};
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  }

  &:disabled {
    opacity: 0.5;
    cursor: default;
  }
`;

const SavedBadge = styled.span`
  font-size: ${({ theme }) => theme.fontSizes.xs};
  color: ${({ theme }) => theme.colors.success};
  margin-left: 8px;
`;

function ModelSelector({
  providers,
  settings,
  saving,
  onSelectProvider,
  onSelectModel,
  onSelectEmbedModel,
}) {
  const currentProvider = settings.default_provider || '';
  const currentModel = settings.default_model || '';
  const currentEmbedModel = settings.embed_model || '';

  const selectedProviderObj = providers.find((p) => p.name === currentProvider);
  const availableModels = selectedProviderObj?.models || [];

  // Only OpenAI has embed_models
  const openaiProvider = providers.find((p) => p.name === 'openai');
  const embedModels = openaiProvider?.embed_models || [];

  function handleProviderChange(e) {
    const newProvider = e.target.value;
    onSelectProvider(newProvider);
    // Reset model when provider changes
    const newProviderObj = providers.find((p) => p.name === newProvider);
    const firstModel = newProviderObj?.models?.[0] || '';
    if (firstModel) {
      onSelectModel(firstModel);
    }
  }

  function handleModelChange(e) {
    onSelectModel(e.target.value);
  }

  function handleEmbedModelChange(e) {
    onSelectEmbedModel(e.target.value);
  }

  return (
    <Grid>
      <Field>
        <Label htmlFor="default-provider">
          Default Provider
          {saving.default_provider === 'saved' && <SavedBadge>Saved</SavedBadge>}
        </Label>
        <SubLabel>LLM provider used for chat</SubLabel>
        <Select
          id="default-provider"
          value={currentProvider}
          onChange={handleProviderChange}
        >
          <option value="" disabled>Select provider…</option>
          {providers.map((p) => (
            <option key={p.name} value={p.name}>
              {p.display_name}
            </option>
          ))}
        </Select>
      </Field>

      <Field>
        <Label htmlFor="default-model">
          Default Model
          {saving.default_model === 'saved' && <SavedBadge>Saved</SavedBadge>}
        </Label>
        <SubLabel>Model to use for responses</SubLabel>
        <Select
          id="default-model"
          value={currentModel}
          onChange={handleModelChange}
          disabled={availableModels.length === 0}
        >
          <option value="" disabled>Select model…</option>
          {availableModels.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </Select>
      </Field>

      <Field>
        <Label htmlFor="embed-model">
          Embedding Model
          {saving.embed_model === 'saved' && <SavedBadge>Saved</SavedBadge>}
        </Label>
        <SubLabel>OpenAI model for document indexing</SubLabel>
        <Select
          id="embed-model"
          value={currentEmbedModel}
          onChange={handleEmbedModelChange}
          disabled={embedModels.length === 0}
        >
          <option value="" disabled>Select embed model…</option>
          {embedModels.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </Select>
      </Field>
    </Grid>
  );
}

export default ModelSelector;
