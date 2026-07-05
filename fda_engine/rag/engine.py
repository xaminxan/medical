"""RAG engine — LlamaIndex + ChromaDB integration with dual-space vector storage."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger


class RAGEngine:
    """Unified RAG engine with LlamaIndex and ChromaDB.

    Dual spaces:
    - product_tech: Ground truth from source technical documents
    - qms_law: QMS and regulatory reference documents
    """

    def __init__(self, db_path: str = "~/.fda_engine/vector_db"):
        self.db_path = Path(db_path).expanduser()
        self._client = None
        self._vector_store = None
        self._product_index = None
        self._law_index = None
        self._initialized = False

    async def initialize(self):
        """Initialize ChromaDB + LlamaIndex."""
        if self._initialized:
            return

        try:
            import chromadb
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.core import VectorStoreIndex, StorageContext
            from llama_index.core.embeddings import resolve_embed_model

            self.db_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self.db_path))

            # Use local embedding model (no API key needed)
            try:
                embed_model = resolve_embed_model("local:BAAI/bge-small-en-v1.5")
            except Exception:
                embed_model = None

            # Product tech space
            product_collection = self._client.get_or_create_collection(
                name="product_tech",
                metadata={"hnsw:space": "cosine"},
            )
            product_store = ChromaVectorStore(chroma_collection=product_collection)
            product_storage = StorageContext.from_defaults(vector_store=product_store)
            self._product_index = VectorStoreIndex.from_vector_store(
                product_store, storage_context=product_storage,
                embed_model=embed_model,
            )

            # QMS law space
            law_collection = self._client.get_or_create_collection(
                name="qms_law",
                metadata={"hnsw:space": "cosine"},
            )
            law_store = ChromaVectorStore(chroma_collection=law_collection)
            law_storage = StorageContext.from_defaults(vector_store=law_store)
            self._law_index = VectorStoreIndex.from_vector_store(
                law_store, storage_context=law_storage,
                embed_model=embed_model,
            )

            self._initialized = True
            logger.info(f"RAG engine initialized at {self.db_path}")
        except ImportError as e:
            logger.warning(f"Missing dependencies for RAG: {e}")
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")

    async def add_document(
        self,
        space: str,
        doc_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ):
        """Add a document to a vector space using LlamaIndex."""
        index = self._get_index(space)
        if index is None:
            return

        from llama_index.core import Document

        doc = Document(
            text=content,
            id_=doc_id,
            metadata={"doc_id": doc_id, **(metadata or {})},
        )

        index.insert(doc)
        logger.debug(f"Added document '{doc_id}' to '{space}'")

    async def add_documents_batch(
        self,
        space: str,
        documents: list[dict[str, Any]],
    ):
        """Add multiple documents in batch."""
        index = self._get_index(space)
        if index is None:
            return

        from llama_index.core import Document

        docs = [
            Document(
                text=d["content"],
                id_=d["doc_id"],
                metadata={"doc_id": d["doc_id"], **d.get("metadata", {})},
            )
            for d in documents
        ]

        for doc in docs:
            index.insert(doc)
        logger.info(f"Added {len(docs)} documents to '{space}'")

    async def query(
        self,
        space: str,
        question: str,
        n_results: int = 5,
        where: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Query a vector space using LlamaIndex retriever."""
        index = self._get_index(space)
        if index is None:
            return []

        retriever = index.as_retriever(similarity_top_k=n_results)
        nodes = retriever.retrieve(question)

        output = []
        for node in nodes:
            output.append({
                "content": node.text,
                "metadata": node.metadata,
                "score": node.score if hasattr(node, "score") else 0,
            })

        return output

    async def query_with_filter(
        self,
        space: str,
        question: str,
        doc_ids: list[str] | None = None,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Query with metadata filters."""
        index = self._get_index(space)
        if index is None:
            return []

        from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters

        filters = None
        if doc_ids:
            filters = MetadataFilters(
                filters=[ExactMatchFilter(key="doc_id", value=did) for did in doc_ids]
            )

        retriever = index.as_retriever(
            similarity_top_k=n_results,
            filters=filters,
        )
        nodes = retriever.retrieve(question)

        return [
            {
                "content": node.text,
                "metadata": node.metadata,
                "score": node.score if hasattr(node, "score") else 0,
            }
            for node in nodes
        ]

    def _get_index(self, space: str):
        """Get LlamaIndex by space name."""
        if space == "product_tech":
            return self._product_index
        elif space == "qms_law":
            return self._law_index
        return None
