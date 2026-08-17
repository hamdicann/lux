"""
LUX — Document Ingestion Script

Run this to ingest documents from the documents/ directory
into the LUX knowledge base.

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --path documents/sample/
    python scripts/ingest.py --clear  (re-index everything)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from app.config import config


def main():
    parser = argparse.ArgumentParser(description="LUX Document Ingestion")
    parser.add_argument("--path", type=str, default=None, help="Directory to ingest")
    parser.add_argument("--clear", action="store_true", help="Clear existing data first")
    args = parser.parse_args()

    config.ensure_directories()

    print("LUX — Document Ingestion")
    print("=" * 40)

    # Initialize components
    from storage.database import DatabaseManager
    from llm.foundry_client import FoundryClient
    from llm.embeddings import EmbeddingService
    from rag.ingestion import IngestionPipeline

    print("Initializing database...")
    db = DatabaseManager(config.database_path)
    db.initialize()

    print("Initializing Foundry Local...")
    foundry = FoundryClient(config)
    foundry.initialize()

    print(f"Loading embedding model ({config.embedding_model})...")
    foundry.load_embedding_model()

    embeddings = EmbeddingService(foundry, config)
    pipeline = IngestionPipeline(config, db, embeddings)

    if args.clear:
        print("Clearing existing data...")
        pipeline.clear_all()

    directory = Path(args.path) if args.path else config.document_path
    print(f"\nIngesting from: {directory}")
    print("-" * 40)

    result = pipeline.ingest_directory(directory)

    print(f"\nResults:")
    print(f"  Files found:  {result.total_files}")
    print(f"  Ingested:     {result.ingested}")
    print(f"  Skipped:      {result.skipped}")
    print(f"  Failed:       {result.failed}")
    print(f"  Total chunks: {result.total_chunks}")
    print(f"  Duration:     {result.duration}s")

    if result.errors:
        print(f"\nErrors:")
        for err in result.errors:
            print(f"  - {err}")

    stats = db.get_stats()
    print(f"\nKnowledge Base:")
    print(f"  Documents: {stats['documents']}")
    print(f"  Chunks:    {stats['chunks']}")
    print(f"  DB Size:   {stats['database_size_mb']} MB")

    db.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
