"""
Enhanced Cache Management System
Provides robust caching with validation, expiration, and corruption handling
"""

import os
import json
import hashlib
import pickle
import time
import shutil
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int
    size_bytes: int
    checksum: str
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = None


class CacheManager:
    """Advanced cache management system"""
    
    def __init__(self, cache_dir: str = "./cache", 
                 max_size_mb: int = 1000,
                 default_ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = timedelta(hours=default_ttl_hours)
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache database
        self.db_path = self.cache_dir / "cache.db"
        self._init_database()
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'corrupted': 0
        }
        
        # Thread lock for concurrent access
        self.lock = threading.Lock()
        
        # Clean up on initialization
        self._cleanup_expired()
    
    def _init_database(self):
        """Initialize SQLite database for cache metadata"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                filename TEXT,
                created_at REAL,
                accessed_at REAL,
                access_count INTEGER,
                size_bytes INTEGER,
                checksum TEXT,
                expires_at REAL,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate checksum for data integrity"""
        return hashlib.md5(data).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from cache"""
        with self.lock:
            try:
                # Check database for entry
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT filename, checksum, expires_at, access_count 
                    FROM cache_entries WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                
                if not row:
                    self.stats['misses'] += 1
                    conn.close()
                    return default
                
                filename, expected_checksum, expires_at, access_count = row
                
                # Check expiration
                if expires_at and expires_at < time.time():
                    self._remove_entry(key)
                    self.stats['misses'] += 1
                    conn.close()
                    return default
                
                # Load cached file
                cache_file = self.cache_dir / filename
                if not cache_file.exists():
                    logger.warning(f"Cache file missing: {filename}")
                    self._remove_entry(key)
                    self.stats['misses'] += 1
                    conn.close()
                    return default
                
                # Read and validate data
                data = cache_file.read_bytes()
                actual_checksum = self._calculate_checksum(data)
                
                if actual_checksum != expected_checksum:
                    logger.warning(f"Cache corruption detected for key: {key}")
                    self._remove_entry(key)
                    self.stats['corrupted'] += 1
                    conn.close()
                    return default
                
                # Deserialize data
                try:
                    value = pickle.loads(data)
                except Exception as e:
                    logger.error(f"Failed to deserialize cache: {e}")
                    self._remove_entry(key)
                    conn.close()
                    return default
                
                # Update access statistics
                cursor.execute("""
                    UPDATE cache_entries 
                    SET accessed_at = ?, access_count = ?
                    WHERE key = ?
                """, (time.time(), access_count + 1, key))
                
                conn.commit()
                conn.close()
                
                self.stats['hits'] += 1
                return value
                
            except Exception as e:
                logger.error(f"Cache get error: {e}")
                return default
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None,
           metadata: Dict[str, Any] = None) -> bool:
        """Set item in cache"""
        with self.lock:
            try:
                # Serialize data
                data = pickle.dumps(value)
                size_bytes = len(data)
                
                # Check size limit
                if size_bytes > self.max_size_bytes * 0.1:  # Single item limit: 10% of total
                    logger.warning(f"Cache item too large: {size_bytes} bytes")
                    return False
                
                # Ensure cache size limit
                self._ensure_space(size_bytes)
                
                # Calculate checksum
                checksum = self._calculate_checksum(data)
                
                # Generate filename
                filename = f"{key[:8]}_{int(time.time())}.cache"
                cache_file = self.cache_dir / filename
                
                # Write to file
                cache_file.write_bytes(data)
                
                # Calculate expiration
                ttl = ttl or self.default_ttl
                expires_at = time.time() + ttl.total_seconds() if ttl else None
                
                # Store metadata in database
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, filename, created_at, accessed_at, access_count, 
                     size_bytes, checksum, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key, filename, time.time(), time.time(), 0,
                    size_bytes, checksum, expires_at,
                    json.dumps(metadata) if metadata else None
                ))
                
                conn.commit()
                conn.close()
                
                return True
                
            except Exception as e:
                logger.error(f"Cache set error: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self.lock:
            return self._remove_entry(key)
    
    def _remove_entry(self, key: str) -> bool:
        """Remove cache entry and file"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get filename
            cursor.execute("SELECT filename FROM cache_entries WHERE key = ?", (key,))
            row = cursor.fetchone()
            
            if row:
                filename = row[0]
                cache_file = self.cache_dir / filename
                
                # Delete file
                if cache_file.exists():
                    cache_file.unlink()
                
                # Delete database entry
                cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove cache entry: {e}")
            return False
    
    def _ensure_space(self, required_bytes: int):
        """Ensure enough space in cache (LRU eviction)"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get current cache size
        cursor.execute("SELECT SUM(size_bytes) FROM cache_entries")
        current_size = cursor.fetchone()[0] or 0
        
        # Check if eviction needed
        if current_size + required_bytes > self.max_size_bytes:
            # Get entries sorted by least recently used
            cursor.execute("""
                SELECT key, size_bytes 
                FROM cache_entries 
                ORDER BY accessed_at ASC
            """)
            
            space_to_free = (current_size + required_bytes) - self.max_size_bytes
            freed = 0
            
            for key, size in cursor.fetchall():
                if freed >= space_to_free:
                    break
                
                self._remove_entry(key)
                freed += size
                self.stats['evictions'] += 1
                logger.debug(f"Evicted cache entry: {key}")
        
        conn.close()
    
    def _cleanup_expired(self):
        """Clean up expired cache entries"""
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                
                current_time = time.time()
                
                # Get expired entries
                cursor.execute("""
                    SELECT key FROM cache_entries 
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                """, (current_time,))
                
                expired_keys = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                # Remove expired entries
                for key in expired_keys:
                    self._remove_entry(key)
                    logger.debug(f"Cleaned up expired cache: {key}")
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                    
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            try:
                # Delete all cache files
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
                
                # Clear database
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cache_entries")
                conn.commit()
                conn.close()
                
                logger.info("Cache cleared")
                
            except Exception as e:
                logger.error(f"Failed to clear cache: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Get cache metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_entries,
                SUM(size_bytes) as total_size,
                AVG(access_count) as avg_access_count,
                MAX(accessed_at) as last_access
            FROM cache_entries
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        total_entries, total_size, avg_access, last_access = row
        
        hit_rate = (self.stats['hits'] / 
                   max(self.stats['hits'] + self.stats['misses'], 1))
        
        return {
            'total_entries': total_entries or 0,
            'total_size_mb': (total_size or 0) / 1024 / 1024,
            'max_size_mb': self.max_size_bytes / 1024 / 1024,
            'usage_percent': ((total_size or 0) / self.max_size_bytes * 100),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self.stats['evictions'],
            'corrupted': self.stats['corrupted'],
            'avg_access_count': avg_access or 0,
            'last_access': datetime.fromtimestamp(last_access).isoformat() if last_access else None
        }
    
    def export_cache_report(self, output_path: str = "cache_report.json"):
        """Export detailed cache report"""
        stats = self.get_statistics()
        
        # Get top accessed entries
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key, access_count, size_bytes, created_at
            FROM cache_entries
            ORDER BY access_count DESC
            LIMIT 10
        """)
        
        top_entries = [
            {
                'key': row[0][:16] + '...',
                'access_count': row[1],
                'size_kb': row[2] / 1024,
                'created': datetime.fromtimestamp(row[3]).isoformat()
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        report = {
            'generated': datetime.now().isoformat(),
            'statistics': stats,
            'top_accessed': top_entries
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Cache report exported to {output_path}")


def cached(cache_manager: CacheManager = None, 
          ttl: Optional[timedelta] = None,
          key_func: Optional[Callable] = None):
    """Decorator for automatic caching"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided cache or create new one
            cache = cache_manager or getattr(wrapper, '_cache', None)
            if not cache:
                cache = CacheManager()
                wrapper._cache = cache
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._generate_key(
                    func.__module__, func.__name__, *args, **kwargs
                )
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


class PDFCache:
    """Specialized cache for PDF files"""
    
    def __init__(self, cache_dir: str = "./cache/pdfs"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_manager = CacheManager(cache_dir=str(self.cache_dir))
    
    def cache_pdf(self, url: str, pdf_content: bytes, metadata: Dict[str, Any] = None) -> bool:
        """Cache a PDF file"""
        # Generate cache key from URL
        cache_key = hashlib.sha256(url.encode()).hexdigest()
        
        # Store PDF with metadata
        cache_data = {
            'url': url,
            'content': pdf_content,
            'size': len(pdf_content),
            'cached_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        return self.cache_manager.set(
            cache_key, 
            cache_data,
            ttl=timedelta(days=7)  # PDFs cached for 7 days
        )
    
    def get_pdf(self, url: str) -> Optional[bytes]:
        """Get cached PDF"""
        cache_key = hashlib.sha256(url.encode()).hexdigest()
        cache_data = self.cache_manager.get(cache_key)
        
        if cache_data:
            return cache_data.get('content')
        return None
    
    def is_cached(self, url: str) -> bool:
        """Check if PDF is cached"""
        cache_key = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_manager.get(cache_key) is not None