import { useState, useEffect, useCallback } from 'react';
import { useBridge } from './useBridge';

export function useSettings() {
  const { call } = useBridge();
  const [providers, setProviders] = useState([]);
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [providerList, settingsList] = await Promise.all([
          call('get_providers'),
          call('get_settings'),
        ]);
        setProviders(providerList || []);
        // Convert list of {key, value} into a plain object
        const map = {};
        for (const s of settingsList || []) {
          map[s.key] = s.value;
        }
        setSettings(map);
      } catch (err) {
        console.error('[useSettings] load failed:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [call]);

  const saveApiKey = useCallback(
    async (provider, apiKey) => {
      const key = `apiKey_${provider}`;
      setSaving((prev) => ({ ...prev, [key]: 'saving' }));
      try {
        await call('set_api_key', provider, apiKey);
        setSaving((prev) => ({ ...prev, [key]: 'saved' }));
        setTimeout(() => {
          setSaving((prev) => ({ ...prev, [key]: null }));
        }, 2000);
      } catch (err) {
        console.error('[useSettings] saveApiKey failed:', err);
        setSaving((prev) => ({ ...prev, [key]: 'error' }));
      }
    },
    [call]
  );

  const saveSetting = useCallback(
    async (settingKey, value) => {
      setSaving((prev) => ({ ...prev, [settingKey]: 'saving' }));
      try {
        await call('set_setting', settingKey, value);
        setSettings((prev) => ({ ...prev, [settingKey]: value }));
        setSaving((prev) => ({ ...prev, [settingKey]: 'saved' }));
        setTimeout(() => {
          setSaving((prev) => ({ ...prev, [settingKey]: null }));
        }, 2000);
      } catch (err) {
        console.error('[useSettings] saveSetting failed:', err);
        setSaving((prev) => ({ ...prev, [settingKey]: 'error' }));
      }
    },
    [call]
  );

  const selectDefaultProvider = useCallback(
    (provider) => saveSetting('default_provider', provider),
    [saveSetting]
  );

  const selectDefaultModel = useCallback(
    (model) => saveSetting('default_model', model),
    [saveSetting]
  );

  const selectEmbedModel = useCallback(
    (model) => saveSetting('embed_model', model),
    [saveSetting]
  );

  return {
    providers,
    settings,
    loading,
    saving,
    saveApiKey,
    saveSetting,
    selectDefaultProvider,
    selectDefaultModel,
    selectEmbedModel,
  };
}
