#!/usr/bin/env python3
"""
Setup script to upload Bluebook.json to OpenAI vector store.
Run this once to initialize the vector store.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from src.vector_store_manager import VectorStoreManager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Upload Bluebook to vector store."""
    logger.info("Starting vector store setup...")

    # Initialize manager
    manager = VectorStoreManager(
        api_key=settings.OPENAI_API_KEY,
        cache_file=settings.VECTOR_STORE_CACHE
    )

    # Check if we already have an assistant
    existing_assistant_id = manager.get_assistant_id()
    if existing_assistant_id:
        logger.info(f"Assistant already exists: {existing_assistant_id}")
        response = input("Do you want to delete and recreate it? (y/N): ")
        if response.lower() == 'y':
            manager.delete_assistant()
        else:
            logger.info("Using existing assistant.")
            return

    # Upload Bluebook
    logger.info(f"Uploading Bluebook from: {settings.BLUEBOOK_JSON_PATH}")
    assistant_id = manager.upload_bluebook(settings.BLUEBOOK_JSON_PATH)

    logger.info(f"✓ Assistant created successfully!")
    logger.info(f"✓ Assistant ID: {assistant_id}")
    logger.info(f"✓ Vector store ID: {manager.get_vector_store_id()}")
    logger.info(f"✓ Cached at: {settings.VECTOR_STORE_CACHE}")
    logger.info("\nYou can now use the File Search tool in citation validation.")


if __name__ == "__main__":
    main()
