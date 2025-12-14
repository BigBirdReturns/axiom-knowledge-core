"""
vector_store.py
===============

A wrapper around the [Chroma](https://www.trychroma.com/) vector database for
retrieval‑augmented generation (RAG).  Chroma stores embeddings and metadata in
a local directory, allowing fast similarity search without any network
dependency.  This module provides a thin abstraction that handles embedding
documents and queries using a configurable sentence transformer model.

Example usage:

>>> vs = VectorStore(db_path="data/embeddings", collection_name="corpus")
>>> vs.add_texts(["Hello world"], metadatas=[{"source": "greeting"}])
>>> results = vs.query("hello")
>>> print(results[0]["document"])

The default embedding model is `all-MiniLM-L6-v2`.  This model will be
downloaded on first use; to run fully offline you should pre‑cache it in
`~/.cache/sentence_transformers/`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


@dataclass
class SearchResult:
    document: str
    metadata: Dict
    distance: float


class VectorStore:
    """Thin wrapper around Chroma for storing and retrieving text embeddings.

    Parameters
    ----------
    db_path: str
        Path to the directory where Chroma will persist its data.  If the
        directory does not exist it will be created.
    collection_name: str
        Name of the collection in which to store embeddings.  Collections allow
        multiple independent indexes in the same database.
    embed_model_name: str, optional
        Name of the sentence transformer model to use for embeddings.  Defaults
        to `all-MiniLM-L6-v2`.
    """

    def __init__(
        self,
        db_path: str,
        collection_name: str,
        embed_model_name: str = None,
    ) -> None:
        self.db_path = os.path.abspath(db_path)
        os.makedirs(self.db_path, exist_ok=True)
        # Configure Chroma to run in persistent mode
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=self.db_path,
        )
        self.client = chromadb.Client(settings)
        self.collection = self.client.get_or_create_collection(name=collection_name)
        # Choose a multilingual embedding model by default.  If a specific
        # ``embed_model_name`` is provided, use that; otherwise fall back to a
        # multilingual MiniLM model that supports cross‑lingual retrieval.
        model_name = embed_model_name or "paraphrase-multilingual-MiniLM-L12-v2"
        self.embed_model = SentenceTransformer(model_name)

    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> None:
        """Add a batch of documents to the vector store.

        Each text will be embedded using the sentence transformer model.  The
        resulting vectors are stored along with the original text and optional
        metadata.  A unique ID is generated for each document.

        Parameters
        ----------
        texts: list of str
            Documents to embed and store.
        metadatas: list of dict, optional
            Optional metadata associated with each document.  Must be the same
            length as `texts` if provided.
        """
        if metadatas is None:
            metadatas = [{} for _ in texts]
        if len(metadatas) != len(texts):
            raise ValueError("Length of metadatas must match length of texts")
        # Compute embeddings
        embeddings = self.embed_model.encode(texts, convert_to_numpy=True).tolist()
        # Use simple numeric IDs
        ids = [f"doc-{self.collection.count() + i}" for i in range(len(texts))]
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        # Persist changes to disk
        self.client.persist()

    def query(self, query: str, k: int = 3) -> List[SearchResult]:
        """Search the vector store for documents similar to the query.

        Parameters
        ----------
        query: str
            The search query.
        k: int
            Maximum number of results to return.

        Returns
        -------
        list of SearchResult
            A list of results sorted by increasing distance (lower is more similar).
        """
        query_embedding = self.embed_model.encode([query], convert_to_numpy=True).tolist()[0]
        results = self.collection.query(query_embeddings=[query_embedding], n_results=k, include=["documents", "metadatas", "distances"])
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        return [SearchResult(document=d, metadata=m, distance=dist) for d, m, dist in zip(docs, metas, dists)]

    def count(self) -> int:
        """Return the number of vectors in the collection."""
        return self.collection.count()


__all__ = ["VectorStore", "SearchResult"]