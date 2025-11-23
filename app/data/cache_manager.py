"""
Cache manager with SQLite backend for efficient storage and retrieval
"""
import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages local cache with SQLite database"""

    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / "cache.db"
        self._initialize_database()

        logger.info(f"Initialized cache manager at {self.cache_dir}")

    def _initialize_database(self):
        """Initialize SQLite database with schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Articles table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        article_id TEXT PRIMARY KEY,
                        volume_issue TEXT,
                        author TEXT,
                        title TEXT,
                        stage TEXT,
                        drive_link TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Sources table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sources (
                        source_id TEXT PRIMARY KEY,
                        article_id TEXT,
                        citation TEXT,
                        source_type TEXT,
                        footnote_number INTEGER,
                        status TEXT,
                        drive_link TEXT,
                        r1_drive_link TEXT,
                        database TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles(article_id)
                    )
                ''')

                # Validation results table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS validation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id TEXT,
                        citation TEXT,
                        footnote_number INTEGER,
                        format_issues TEXT,  -- JSON
                        format_suggestion TEXT,
                        support_issues TEXT,  -- JSON
                        confidence_score INTEGER,
                        requires_review BOOLEAN,
                        review_reason TEXT,
                        proposition TEXT,
                        source_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_id) REFERENCES sources(source_id)
                    )
                ''')

                # File cache table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file_cache (
                        file_id TEXT PRIMARY KEY,
                        source_id TEXT,
                        file_type TEXT,  -- pdf, r1_pdf, etc.
                        file_path TEXT,
                        file_size INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_id) REFERENCES sources(source_id)
                    )
                ''')

                # Processing metadata table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processing_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id TEXT,
                        stage TEXT,
                        success_count INTEGER,
                        fail_count INTEGER,
                        total INTEGER,
                        errors TEXT,  -- JSON
                        warnings TEXT,  -- JSON
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles(article_id)
                    )
                ''')

                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sources_article ON sources(article_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_validation_source ON validation_results(source_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_cache_source ON file_cache(source_id)')

                conn.commit()
                logger.debug("Database schema initialized")

        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
            raise

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Return rows as dicts
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}", exc_info=True)
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    # Article operations
    def save_article(self, article_data: Dict):
        """Save or update article in cache"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO articles
                    (article_id, volume_issue, author, title, stage, drive_link, error_message, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    article_data['article_id'],
                    article_data.get('volume_issue', ''),
                    article_data.get('author', ''),
                    article_data.get('title', ''),
                    article_data.get('stage', 'not_started'),
                    article_data.get('drive_link'),
                    article_data.get('error_message')
                ))
                conn.commit()
                logger.debug(f"Saved article {article_data['article_id']} to cache")

        except sqlite3.Error as e:
            logger.error(f"Error saving article: {e}", exc_info=True)
            raise

    def get_article(self, article_id: str) -> Optional[Dict]:
        """Retrieve article from cache"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM articles WHERE article_id = ?', (article_id,))
                row = cursor.fetchone()

                if row:
                    return dict(row)
                return None

        except sqlite3.Error as e:
            logger.error(f"Error getting article: {e}", exc_info=True)
            return None

    def get_all_articles(self) -> List[Dict]:
        """Retrieve all articles from cache"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM articles ORDER BY updated_at DESC')
                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(f"Error getting articles: {e}", exc_info=True)
            return []

    # Source operations
    def save_source(self, source_data: Dict):
        """Save or update source in cache"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO sources
                    (source_id, article_id, citation, source_type, footnote_number,
                     status, drive_link, r1_drive_link, database, error_message, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    source_data['source_id'],
                    source_data['article_id'],
                    source_data['citation'],
                    source_data.get('source_type', 'case'),
                    source_data.get('footnote_number'),
                    source_data.get('status', 'pending'),
                    source_data.get('drive_link'),
                    source_data.get('r1_drive_link'),
                    source_data.get('database'),
                    source_data.get('error_message')
                ))
                conn.commit()
                logger.debug(f"Saved source {source_data['source_id']} to cache")

        except sqlite3.Error as e:
            logger.error(f"Error saving source: {e}", exc_info=True)
            raise

    def get_source(self, source_id: str) -> Optional[Dict]:
        """Retrieve source from cache"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM sources WHERE source_id = ?', (source_id,))
                row = cursor.fetchone()

                if row:
                    return dict(row)
                return None

        except sqlite3.Error as e:
            logger.error(f"Error getting source: {e}", exc_info=True)
            return None

    def get_sources_for_article(self, article_id: str) -> List[Dict]:
        """Retrieve all sources for an article"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM sources WHERE article_id = ? ORDER BY footnote_number',
                    (article_id,)
                )
                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as e:
            logger.error(f"Error getting sources: {e}", exc_info=True)
            return []

    # Validation operations
    def save_validation_result(self, validation_data: Dict):
        """Save validation result"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO validation_results
                    (source_id, citation, footnote_number, format_issues, format_suggestion,
                     support_issues, confidence_score, requires_review, review_reason,
                     proposition, source_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    validation_data['source_id'],
                    validation_data['citation'],
                    validation_data.get('footnote_number'),
                    json.dumps(validation_data.get('format_issues', [])),
                    validation_data.get('format_suggestion'),
                    json.dumps(validation_data.get('support_issues', [])),
                    validation_data.get('confidence_score', 0),
                    validation_data.get('requires_review', False),
                    validation_data.get('review_reason'),
                    validation_data.get('proposition'),
                    validation_data.get('source_text')
                ))
                conn.commit()
                logger.debug(f"Saved validation result for {validation_data['source_id']}")

        except sqlite3.Error as e:
            logger.error(f"Error saving validation result: {e}", exc_info=True)
            raise

    def get_validation_results(self, article_id: str) -> List[Dict]:
        """Get all validation results for an article"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT v.* FROM validation_results v
                    JOIN sources s ON v.source_id = s.source_id
                    WHERE s.article_id = ?
                    ORDER BY v.footnote_number
                ''', (article_id,))

                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    # Parse JSON fields
                    result['format_issues'] = json.loads(result['format_issues'])
                    result['support_issues'] = json.loads(result['support_issues'])
                    results.append(result)

                return results

        except sqlite3.Error as e:
            logger.error(f"Error getting validation results: {e}", exc_info=True)
            return []

    # File cache operations
    def cache_file(self, file_id: str, source_id: str, file_type: str, file_path: str):
        """Record cached file"""
        try:
            file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO file_cache
                    (file_id, source_id, file_type, file_path, file_size, last_accessed)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (file_id, source_id, file_type, file_path, file_size))
                conn.commit()
                logger.debug(f"Cached file {file_id} at {file_path}")

        except sqlite3.Error as e:
            logger.error(f"Error caching file: {e}", exc_info=True)
            raise

    def get_cached_file(self, file_id: str) -> Optional[str]:
        """Get path to cached file if it exists"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT file_path FROM file_cache WHERE file_id = ?',
                    (file_id,)
                )
                row = cursor.fetchone()

                if row:
                    file_path = row['file_path']
                    if Path(file_path).exists():
                        # Update last accessed time
                        cursor.execute(
                            'UPDATE file_cache SET last_accessed = CURRENT_TIMESTAMP WHERE file_id = ?',
                            (file_id,)
                        )
                        conn.commit()
                        return file_path

                return None

        except sqlite3.Error as e:
            logger.error(f"Error getting cached file: {e}", exc_info=True)
            return None

    def clear_old_cache(self, days: int = 30):
        """Clear cache entries older than specified days"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get files to delete
                cursor.execute('''
                    SELECT file_path FROM file_cache
                    WHERE last_accessed < datetime('now', '-{} days')
                '''.format(days))

                files_to_delete = [row['file_path'] for row in cursor.fetchall()]

                # Delete from database
                cursor.execute('''
                    DELETE FROM file_cache
                    WHERE last_accessed < datetime('now', '-{} days')
                '''.format(days))

                conn.commit()

                # Delete actual files
                deleted_count = 0
                for file_path in files_to_delete:
                    try:
                        if Path(file_path).exists():
                            Path(file_path).unlink()
                            deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {file_path}: {e}")

                logger.info(f"Cleared {deleted_count} old cache files")

        except sqlite3.Error as e:
            logger.error(f"Error clearing cache: {e}", exc_info=True)

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                cursor.execute('SELECT COUNT(*) as count FROM articles')
                stats['articles_count'] = cursor.fetchone()['count']

                cursor.execute('SELECT COUNT(*) as count FROM sources')
                stats['sources_count'] = cursor.fetchone()['count']

                cursor.execute('SELECT COUNT(*) as count FROM validation_results')
                stats['validations_count'] = cursor.fetchone()['count']

                cursor.execute('SELECT COUNT(*) as count, SUM(file_size) as total_size FROM file_cache')
                row = cursor.fetchone()
                stats['cached_files_count'] = row['count']
                stats['total_cache_size_bytes'] = row['total_size'] or 0
                stats['total_cache_size_mb'] = round((row['total_size'] or 0) / (1024 * 1024), 2)

                return stats

        except sqlite3.Error as e:
            logger.error(f"Error getting cache stats: {e}", exc_info=True)
            return {}
