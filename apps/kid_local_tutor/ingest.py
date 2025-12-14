"""
ingest.py
=========

This script ingests educational documents into the local vector store.  It reads
text files (and optionally other formats) from a specified directory, splits
them into manageable chunks, computes embeddings using a sentence transformer,
and stores them in a persistent ChromaDB collection.  The resulting index
enables retrieval‑augmented generation when answering questions.

Usage from the command line:

```
python -m kid_local_tutor.ingest --docs data/docs --db data/embeddings --name corpus
```

This will create a Chroma database at `data/embeddings` with a collection
named `corpus`, and populate it with the documents found in `data/docs`.

Note: Only `.txt` files are processed by default.  To support PDFs, implement
loading in `utils.load_document` or convert them to text before ingestion.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

from .vector_store import VectorStore
from .utils import load_document, chunk_text


def ingest_documents(doc_dir: str | Path, db_path: str | Path, collection_name: str,
                     chunk_size: int = 512, overlap: int = 50) -> None:
    """Ingest all documents from a directory into a Chroma vector store.

    Parameters
    ----------
    doc_dir: str or Path
        Directory containing text files to ingest.  Only files ending in
        `.txt` are processed by default.  Subdirectories are ignored.
    db_path: str or Path
        Directory to store the Chroma database.
    collection_name: str
        Name of the Chroma collection to create or use.
    chunk_size: int, optional
        Maximum number of words per chunk.  Passed to `utils.chunk_text`.
    overlap: int, optional
        Number of overlapping words between chunks.  Passed to `utils.chunk_text`.
    """
    doc_dir = Path(doc_dir)
    db_path = Path(db_path)
    # Create the vector store
    vs = VectorStore(str(db_path), collection_name)
    # Gather documents
    docs: List[str] = []
    metas: List[dict] = []
    for file in sorted(doc_dir.iterdir()):
        if file.is_file() and file.suffix.lower() == ".txt":
            text = load_document(file)
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
            for idx, chunk in enumerate(chunks):
                docs.append(chunk)
                metas.append({
                    "source": str(file.name),
                    "chunk_index": idx,
                })
    if not docs:
        print(f"No documents found in {doc_dir}. Nothing to ingest.")
        return
    # Add to the vector store
    print(f"Ingesting {len(docs)} chunks into collection '{collection_name}'...")
    vs.add_texts(docs, metadatas=metas)
    print("Ingestion complete.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest documents into a Chroma vector store.")
    parser.add_argument("--docs", type=str, required=True, help="Directory containing .txt files to ingest.")
    parser.add_argument("--db", type=str, required=True, help="Directory to persist the vector store.")
    parser.add_argument("--name", type=str, default="corpus", help="Collection name (default: corpus).")
    parser.add_argument("--chunk-size", type=int, default=512, help="Number of words per chunk (default: 512).")
    parser.add_argument("--overlap", type=int, default=50, help="Word overlap between chunks (default: 50).")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    ingest_documents(args.docs, args.db, args.name, args.chunk_size, args.overlap)