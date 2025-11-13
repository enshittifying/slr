"""
Vector Store Manager for OpenAI File Search
Handles uploading Bluebook reference files to OpenAI vector store
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict
from openai import OpenAI

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manage OpenAI vector stores for Bluebook reference data."""

    def __init__(self, api_key: str, cache_file: Path = None):
        """
        Initialize vector store manager.

        Args:
            api_key: OpenAI API key
            cache_file: Path to cache file storing vector store ID
        """
        self.client = OpenAI(api_key=api_key)
        self.cache_file = cache_file or Path("config/vector_store_cache.json")
        self.vector_store_id = None
        self.assistant_id = None
        self._load_cache()

    def _load_cache(self):
        """Load vector store ID and assistant ID from cache if exists."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    self.vector_store_id = cache.get('vector_store_id')
                    self.assistant_id = cache.get('assistant_id')
                    logger.info(f"Loaded cached assistant ID: {self.assistant_id}")
                    logger.info(f"Loaded cached vector store ID: {self.vector_store_id}")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save assistant ID and vector store ID to cache."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'assistant_id': self.assistant_id,
                    'vector_store_id': self.vector_store_id,
                    'file_paths': self.uploaded_files
                }, f, indent=2)
            logger.info(f"Saved assistant ID to cache: {self.assistant_id}")
            logger.info(f"Saved vector store ID to cache: {self.vector_store_id}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def upload_bluebook(self, bluebook_path: Path) -> str:
        """
        Upload Bluebook.json to OpenAI and create assistant with file search.

        Args:
            bluebook_path: Path to Bluebook.json file

        Returns:
            Assistant ID
        """
        logger.info(f"Uploading Bluebook file: {bluebook_path}")

        # Check if we already have a vector store
        if self.assistant_id and self.vector_store_id:
            logger.info(f"Using existing assistant: {self.assistant_id}")
            logger.info(f"Using existing vector store: {self.vector_store_id}")
            return self.assistant_id

        try:
            # Upload the file
            with open(bluebook_path, 'rb') as f:
                file_response = self.client.files.create(
                    file=f,
                    purpose='assistants'
                )

            logger.info(f"Uploaded file: {file_response.id}")

            # Create vector store using the assistants v2 API
            # Note: Vector stores are created via assistants API
            assistant = self.client.beta.assistants.create(
                name="Bluebook Citation Assistant",
                instructions="You are an expert in Bluebook legal citation rules. Use the uploaded Bluebook reference to answer questions about citation formatting.",
                model="gpt-4o-mini",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_stores": [{
                            "file_ids": [file_response.id]
                        }]
                    }
                }
            )

            # Extract vector store ID from the assistant
            vector_store_id = assistant.tool_resources.file_search.vector_store_ids[0]

            self.assistant_id = assistant.id
            self.vector_store_id = vector_store_id
            self.uploaded_files = {str(bluebook_path): file_response.id}

            logger.info(f"Created assistant: {self.assistant_id}")
            logger.info(f"Created vector store: {self.vector_store_id}")

            # Save to cache
            self._save_cache()

            return self.assistant_id

        except Exception as e:
            logger.error(f"Failed to upload Bluebook: {e}")
            raise

    def get_assistant_id(self) -> Optional[str]:
        """Get the current assistant ID."""
        return self.assistant_id

    def get_vector_store_id(self) -> Optional[str]:
        """Get the current vector store ID."""
        return self.vector_store_id

    def delete_assistant(self):
        """Delete the assistant (and its vector store) and clear cache."""
        if self.assistant_id:
            try:
                self.client.beta.assistants.delete(self.assistant_id)
                logger.info(f"Deleted assistant: {self.assistant_id}")
                self.assistant_id = None
                self.vector_store_id = None
                if self.cache_file.exists():
                    self.cache_file.unlink()
                logger.info("Cleared cache")
            except Exception as e:
                logger.error(f"Failed to delete assistant: {e}")

    def list_vector_stores(self) -> list:
        """List all vector stores."""
        try:
            stores = self.client.beta.vector_stores.list()
            return stores.data
        except Exception as e:
            logger.error(f"Failed to list vector stores: {e}")
            return []
