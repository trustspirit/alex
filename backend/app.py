from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

try:
    import webview
except ImportError:  # pragma: no cover
    webview = None  # type: ignore[assignment]

from backend.bridge import BridgeAPI
from backend.storage.database import get_engine, get_scoped_session_factory, init_db
from backend.storage.collection_repo import CollectionRepo
from backend.storage.document_repo import DocumentRepo
from backend.storage.chat_repo import ChatRepo
from backend.storage.settings_repo import SettingsRepo
from backend.storage.tag_repo import TagRepo
from backend.llm.provider_manager import ProviderManager
from backend.indexing.store import ChromaStore
from backend.indexing.index_manager import IndexManager
from backend.ingestion.pipeline import IngestionPipeline
from backend.query.query_engine import QueryEngine

DATA_DIR = Path.home() / ".alex"
LOG_DIR = DATA_DIR / "logs"

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure file + stdout logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.handlers.TimedRotatingFileHandler(
                LOG_DIR / "app.log", when="midnight", backupCount=30
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )


def start_app() -> None:
    """Wire all components together and launch the PyWebView window."""
    setup_logging()
    logger.info("Starting Alex …")

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    engine = get_engine(DATA_DIR)
    init_db(engine)
    ScopedSession = get_scoped_session_factory(engine)

    # Pass the scoped session factory — each call to ScopedSession()
    # returns the thread-local session, so repos are thread-safe.
    document_repo = DocumentRepo(ScopedSession)
    collection_repo = CollectionRepo(ScopedSession)
    chat_repo = ChatRepo(ScopedSession)
    settings_repo = SettingsRepo(ScopedSession)
    tag_repo = TagRepo(ScopedSession)

    # ------------------------------------------------------------------
    # LLM provider manager
    # ------------------------------------------------------------------
    provider_manager = ProviderManager()

    # ------------------------------------------------------------------
    # Try to init LLM and embed model from persisted settings
    # ------------------------------------------------------------------
    llm = None
    embed_model = None

    try:
        llm_provider = settings_repo.get("default_provider") or "openai"
        llm_model = settings_repo.get("default_model") or "gpt-4o-mini"
        llm_api_key = settings_repo.get_secret(f"{llm_provider}_api_key") or ""

        if llm_api_key:
            llm = provider_manager.create_llm(llm_provider, llm_model, llm_api_key)
            logger.info("LLM initialised: provider=%s model=%s", llm_provider, llm_model)
        else:
            logger.warning("No API key for provider %r — LLM not initialised.", llm_provider)
    except Exception as exc:
        logger.warning("Could not initialise LLM: %s", exc)

    try:
        embed_provider = settings_repo.get("embed_provider") or "openai"
        embed_model_name = settings_repo.get("embed_model") or "text-embedding-3-small"
        embed_api_key = settings_repo.get_secret(f"{embed_provider}_api_key") or ""

        if embed_api_key:
            embed_model = provider_manager.create_embed_model(
                embed_provider, embed_api_key, embed_model_name
            )
            logger.info(
                "Embed model initialised: provider=%s model=%s",
                embed_provider,
                embed_model_name,
            )
        else:
            logger.warning(
                "No API key for embed provider %r — embed model not initialised.",
                embed_provider,
            )
    except Exception as exc:
        logger.warning("Could not initialise embed model: %s", exc)

    # ------------------------------------------------------------------
    # ChromaDB vector store
    # ------------------------------------------------------------------
    chroma_dir = str(DATA_DIR / "chroma")
    try:
        chroma_store = ChromaStore(persist_dir=chroma_dir)
        vector_store = chroma_store.get_vector_store("default")
        logger.info("ChromaDB store initialised at %s", chroma_dir)
    except Exception as exc:
        logger.warning("ChromaDB not available: %s", exc)
        chroma_store = None  # type: ignore[assignment]
        vector_store = None

    # ------------------------------------------------------------------
    # Index manager (try to load existing index)
    # ------------------------------------------------------------------
    index_manager = IndexManager(
        vector_store=vector_store,
        embed_model=embed_model,
        llm=llm,
    )

    if vector_store is not None:
        try:
            index_manager.load_existing_vector_index()
            logger.info("Existing vector index loaded.")
        except Exception as exc:
            logger.info("No existing vector index to load: %s", exc)

    # ------------------------------------------------------------------
    # Ingestion pipeline
    # ------------------------------------------------------------------
    pipeline = IngestionPipeline(
        document_repo=document_repo,
        index_manager=index_manager,
        llm=llm,
        embed_model=embed_model,
        settings_repo=settings_repo,
    )

    # ------------------------------------------------------------------
    # Query engine
    # ------------------------------------------------------------------
    query_engine = QueryEngine(
        index_manager=index_manager,
        llm=llm,
        document_repo=document_repo,
    )

    # ------------------------------------------------------------------
    # Bridge API
    # ------------------------------------------------------------------
    bridge = BridgeAPI(
        pipeline=pipeline,
        query_engine=query_engine,
        document_repo=document_repo,
        collection_repo=collection_repo,
        chat_repo=chat_repo,
        settings_repo=settings_repo,
        provider_manager=provider_manager,
        tag_repo=tag_repo,
    )

    # ------------------------------------------------------------------
    # Determine frontend URL
    # ------------------------------------------------------------------
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
    if frontend_dist.exists():
        url = str(frontend_dist)
        logger.info("Serving frontend from dist: %s", url)
    else:
        url = "http://localhost:5173"  # Dev mode
        logger.info("Frontend dist not found; using dev server at %s", url)

    # ------------------------------------------------------------------
    # Create PyWebView window
    # ------------------------------------------------------------------
    if webview is None:
        logger.error("pywebview is not installed. Cannot start the UI.")
        return

    window = webview.create_window(
        title="Alex",
        url=url,
        js_api=bridge,
        width=1200,
        height=800,
        min_size=(900, 600),
    )

    bridge.set_window(window)

    logger.info("Starting webview …")
    webview.start(debug=False)
