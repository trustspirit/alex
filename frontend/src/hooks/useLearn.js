import { useState, useEffect, useCallback, useRef } from 'react';
import { useBridge } from './useBridge';
import { useProgress } from './useProgress';

function detectSourceType(filename) {
  const lower = filename.toLowerCase();
  if (lower.endsWith('.pdf')) return 'pdf';
  if (lower.endsWith('.md') || lower.endsWith('.markdown')) return 'md';
  if (lower.endsWith('.txt') || lower.endsWith('.text')) return 'txt';
  return 'txt';
}

function isYoutubeUrl(url) {
  return /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\//.test(url);
}

export function useLearn() {
  const { call } = useBridge();
  const { progress, warnings, errors, dismissWarning, dismissError } = useProgress();

  const [documents, setDocuments] = useState([]);
  const [collections, setCollections] = useState([]);
  const [selectedCollection, setSelectedCollection] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await call('list_documents');
      setDocuments(docs || []);
    } catch (err) {
      console.error('[useLearn] refreshDocuments failed:', err);
    }
  }, [call]);

  const refreshCollections = useCallback(async () => {
    try {
      const cols = await call('list_collections');
      setCollections(cols || []);
    } catch (err) {
      console.error('[useLearn] refreshCollections failed:', err);
    }
  }, [call]);

  useEffect(() => {
    refreshDocuments();
    refreshCollections();
  }, [refreshDocuments, refreshCollections]);

  // Refresh document list when a processing step changes or completes/fails
  const progressStepsRef = useRef({});
  useEffect(() => {
    let shouldRefresh = false;
    for (const [docId, p] of Object.entries(progress)) {
      const prev = progressStepsRef.current[docId];
      if (!prev || prev.step !== p.step) {
        shouldRefresh = true;
      }
    }
    progressStepsRef.current = { ...progress };
    if (shouldRefresh) refreshDocuments();
  }, [progress, refreshDocuments]);

  // Also refresh when errors arrive (document status changed to failed)
  useEffect(() => {
    if (errors.length > 0) refreshDocuments();
  }, [errors, refreshDocuments]);

  // Helper: read a File object as base64 string
  const readFileAsBase64 = (file) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        // result is "data:<mime>;base64,<data>" — strip the prefix
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });

  const uploadFiles = useCallback(
    async (files) => {
      if (!files) {
        // Click: open native OS file dialog via Python bridge
        const result = await call('open_file_dialog');
        if (!result || result.length === 0) return;

        setIsUploading(true);
        try {
          for (const p of result) {
            const name = p.split('/').pop() || p;
            const sourceType = detectSourceType(name);
            await call('ingest_document', p, sourceType, selectedCollection);
          }
          await refreshDocuments();
        } catch (err) {
          console.error('[useLearn] uploadFiles (dialog) failed:', err);
        } finally {
          setIsUploading(false);
        }
        return;
      }

      // Drag & drop: read file contents and send to backend
      setIsUploading(true);
      try {
        for (const file of files) {
          const sourceType = detectSourceType(file.name);
          const base64Content = await readFileAsBase64(file);
          await call('ingest_document_content', file.name, base64Content, sourceType, selectedCollection);
        }
        await refreshDocuments();
      } catch (err) {
        console.error('[useLearn] uploadFiles (drop) failed:', err);
      } finally {
        setIsUploading(false);
      }
    },
    [call, selectedCollection, refreshDocuments]
  );

  const uploadYoutube = useCallback(
    async (url) => {
      if (!isYoutubeUrl(url)) return;
      setIsUploading(true);
      try {
        await call('ingest_document', url, 'youtube', selectedCollection);
        await refreshDocuments();
      } catch (err) {
        console.error('[useLearn] uploadYoutube failed:', err);
      } finally {
        setIsUploading(false);
      }
    },
    [call, selectedCollection, refreshDocuments]
  );

  const deleteDocument = useCallback(
    async (docId) => {
      try {
        await call('delete_document', docId);
        setDocuments((prev) => prev.filter((d) => d.id !== docId));
      } catch (err) {
        console.error('[useLearn] deleteDocument failed:', err);
      }
    },
    [call]
  );

  const reindexDocument = useCallback(
    async (docId) => {
      try {
        await call('reindex_document', docId);
        await refreshDocuments();
      } catch (err) {
        console.error('[useLearn] reindexDocument failed:', err);
      }
    },
    [call, refreshDocuments]
  );

  const selectCollection = useCallback((collId) => {
    setSelectedCollection(collId);
  }, []);

  const createCollection = useCallback(
    async (name) => {
      try {
        const col = await call('create_collection', name);
        if (col) {
          setCollections((prev) => [...prev, col]);
        }
        await refreshCollections();
      } catch (err) {
        console.error('[useLearn] createCollection failed:', err);
      }
    },
    [call, refreshCollections]
  );

  const renameCollection = useCallback(
    async (id, name) => {
      try {
        await call('rename_collection', id, name);
        setCollections((prev) =>
          prev.map((c) => (c.id === id ? { ...c, name } : c))
        );
      } catch (err) {
        console.error('[useLearn] renameCollection failed:', err);
      }
    },
    [call]
  );

  const deleteCollection = useCallback(
    async (id) => {
      try {
        await call('delete_collection', id);
        setCollections((prev) => prev.filter((c) => c.id !== id));
        if (selectedCollection === id) setSelectedCollection(null);
      } catch (err) {
        console.error('[useLearn] deleteCollection failed:', err);
      }
    },
    [call, selectedCollection]
  );

  const filteredDocuments = selectedCollection
    ? documents.filter((d) => d.collection_id === selectedCollection)
    : documents;

  return {
    documents: filteredDocuments,
    allDocuments: documents,
    collections,
    selectedCollection,
    isUploading,
    progress,
    warnings,
    errors,
    dismissWarning,
    dismissError,
    uploadFiles,
    uploadYoutube,
    deleteDocument,
    reindexDocument,
    selectCollection,
    createCollection,
    renameCollection,
    deleteCollection,
    refreshDocuments,
  };
}
