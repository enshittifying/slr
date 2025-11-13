"""
Connection Pool Manager for API calls
Manages connection pooling, rate limiting, and retry logic
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from queue import Queue, Empty
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    calls_per_second: float = 1.0
    calls_per_minute: int = 30
    calls_per_hour: int = 1000
    burst_size: int = 5


@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    name: str
    base_url: str
    api_key: Optional[str] = None
    headers: Dict[str, str] = None
    rate_limit: RateLimitConfig = None
    timeout: int = 30
    max_retries: int = 3


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.max_tokens = config.burst_size
        self.refill_rate = config.calls_per_second
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
        # Tracking for longer periods
        self.minute_calls = []
        self.hour_calls = []
    
    def acquire(self, timeout: float = None) -> bool:
        """Acquire permission to make a request"""
        start_time = time.time()
        timeout = timeout or 60.0
        
        while time.time() - start_time < timeout:
            with self.lock:
                # Refill tokens
                self._refill()
                
                # Check longer period limits
                if not self._check_period_limits():
                    time.sleep(1)
                    continue
                
                # Check if token available
                if self.tokens >= 1:
                    self.tokens -= 1
                    
                    # Record call
                    now = time.time()
                    self.minute_calls.append(now)
                    self.hour_calls.append(now)
                    
                    return True
            
            # Wait before retry
            time.sleep(0.1)
        
        return False
    
    def _refill(self):
        """Refill tokens based on time passed"""
        now = time.time()
        time_passed = now - self.last_refill
        
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def _check_period_limits(self) -> bool:
        """Check minute and hour limits"""
        now = time.time()
        
        # Clean old entries
        self.minute_calls = [t for t in self.minute_calls if now - t < 60]
        self.hour_calls = [t for t in self.hour_calls if now - t < 3600]
        
        # Check limits
        if len(self.minute_calls) >= self.config.calls_per_minute:
            return False
        if len(self.hour_calls) >= self.config.calls_per_hour:
            return False
        
        return True


class ConnectionPool:
    """Manages connection pooling for multiple APIs"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.sessions: Dict[str, requests.Session] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limited': 0,
            'retries': 0
        }
    
    def register_endpoint(self, endpoint: APIEndpoint):
        """Register an API endpoint"""
        with self.lock:
            self.endpoints[endpoint.name] = endpoint
            
            # Create session with connection pooling
            session = self._create_session(endpoint)
            self.sessions[endpoint.name] = session
            
            # Create rate limiter if configured
            if endpoint.rate_limit:
                self.rate_limiters[endpoint.name] = RateLimiter(endpoint.rate_limit)
            
            logger.info(f"Registered endpoint: {endpoint.name}")
    
    def _create_session(self, endpoint: APIEndpoint) -> requests.Session:
        """Create a session with retry logic and connection pooling"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=endpoint.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # Configure adapter with connection pooling
        adapter = HTTPAdapter(
            pool_connections=self.max_connections,
            pool_maxsize=self.max_connections,
            max_retries=retry_strategy,
            pool_block=False
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        if endpoint.headers:
            session.headers.update(endpoint.headers)
        
        # Set API key if provided
        if endpoint.api_key:
            session.headers['Authorization'] = f"Bearer {endpoint.api_key}"
        
        return session
    
    def request(self, endpoint_name: str, method: str, path: str,
               **kwargs) -> Optional[requests.Response]:
        """Make a request to an API endpoint"""
        
        if endpoint_name not in self.endpoints:
            logger.error(f"Unknown endpoint: {endpoint_name}")
            return None
        
        endpoint = self.endpoints[endpoint_name]
        session = self.sessions[endpoint_name]
        
        # Apply rate limiting
        if endpoint_name in self.rate_limiters:
            rate_limiter = self.rate_limiters[endpoint_name]
            if not rate_limiter.acquire(timeout=10):
                logger.warning(f"Rate limit exceeded for {endpoint_name}")
                self.stats['rate_limited'] += 1
                return None
        
        # Prepare request
        url = endpoint.base_url + path
        kwargs.setdefault('timeout', endpoint.timeout)
        
        # Track statistics
        self.stats['total_requests'] += 1
        
        try:
            # Make request
            response = session.request(method, url, **kwargs)
            response.raise_for_status()
            
            self.stats['successful_requests'] += 1
            return response
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited by server
                logger.warning(f"Rate limited by {endpoint_name}: {e}")
                self.stats['rate_limited'] += 1
                
                # Back off
                self._handle_rate_limit(endpoint_name, e.response)
            else:
                logger.error(f"HTTP error from {endpoint_name}: {e}")
                self.stats['failed_requests'] += 1
            
            return None
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {endpoint_name}: {e}")
            self.stats['failed_requests'] += 1
            return None
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout from {endpoint_name}: {e}")
            self.stats['failed_requests'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error from {endpoint_name}: {e}")
            self.stats['failed_requests'] += 1
            return None
    
    def _handle_rate_limit(self, endpoint_name: str, response: requests.Response):
        """Handle rate limit response from server"""
        # Check for Retry-After header
        retry_after = response.headers.get('Retry-After')
        
        if retry_after:
            try:
                # Could be seconds or HTTP date
                wait_time = int(retry_after)
            except ValueError:
                # Parse HTTP date
                from email.utils import parsedate_to_datetime
                retry_date = parsedate_to_datetime(retry_after)
                wait_time = (retry_date - datetime.now()).total_seconds()
            
            logger.info(f"Backing off {endpoint_name} for {wait_time} seconds")
            
            # Adjust rate limiter
            if endpoint_name in self.rate_limiters:
                limiter = self.rate_limiters[endpoint_name]
                # Reduce rate temporarily
                limiter.refill_rate *= 0.5
                
                # Schedule rate recovery
                threading.Timer(
                    wait_time,
                    lambda: setattr(limiter, 'refill_rate', limiter.config.calls_per_second)
                ).start()
    
    def get(self, endpoint_name: str, path: str, **kwargs) -> Optional[requests.Response]:
        """Make a GET request"""
        return self.request(endpoint_name, 'GET', path, **kwargs)
    
    def post(self, endpoint_name: str, path: str, **kwargs) -> Optional[requests.Response]:
        """Make a POST request"""
        return self.request(endpoint_name, 'POST', path, **kwargs)
    
    def close(self):
        """Close all sessions"""
        with self.lock:
            for session in self.sessions.values():
                session.close()
            self.sessions.clear()
            logger.info("Closed all connection pools")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        success_rate = (self.stats['successful_requests'] / 
                       max(self.stats['total_requests'], 1))
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'endpoints': list(self.endpoints.keys()),
            'active_sessions': len(self.sessions)
        }


class APIClient:
    """High-level API client with connection pooling"""
    
    def __init__(self):
        self.pool = ConnectionPool(max_connections=20)
        self._register_default_endpoints()
    
    def _register_default_endpoints(self):
        """Register default API endpoints"""
        
        # CourtListener
        self.pool.register_endpoint(APIEndpoint(
            name='courtlistener',
            base_url='https://www.courtlistener.com/api/rest/v3',
            rate_limit=RateLimitConfig(
                calls_per_second=1,
                calls_per_minute=30,
                calls_per_hour=1000
            )
        ))
        
        # CrossRef
        self.pool.register_endpoint(APIEndpoint(
            name='crossref',
            base_url='https://api.crossref.org',
            rate_limit=RateLimitConfig(
                calls_per_second=2,
                calls_per_minute=50,
                calls_per_hour=2000
            )
        ))
        
        # GovInfo
        self.pool.register_endpoint(APIEndpoint(
            name='govinfo',
            base_url='https://api.govinfo.gov',
            rate_limit=RateLimitConfig(
                calls_per_second=1,
                calls_per_minute=30,
                calls_per_hour=1000
            )
        ))
        
        # Google Books
        self.pool.register_endpoint(APIEndpoint(
            name='google_books',
            base_url='https://www.googleapis.com/books/v1',
            rate_limit=RateLimitConfig(
                calls_per_second=1,
                calls_per_minute=40,
                calls_per_hour=1000
            )
        ))
    
    def search_courtlistener(self, query: str) -> Optional[Dict[str, Any]]:
        """Search CourtListener for cases"""
        response = self.pool.get(
            'courtlistener',
            '/search/',
            params={'q': query, 'type': 'o', 'format': 'json'}
        )
        
        if response:
            return response.json()
        return None
    
    def search_crossref(self, title: str, author: str = None) -> Optional[Dict[str, Any]]:
        """Search CrossRef for articles"""
        params = {'query.title': title}
        if author:
            params['query.author'] = author
        
        response = self.pool.get(
            'crossref',
            '/works',
            params=params
        )
        
        if response:
            return response.json()
        return None
    
    def search_govinfo(self, title: int, section: str) -> Optional[Dict[str, Any]]:
        """Search GovInfo for statutes"""
        response = self.pool.get(
            'govinfo',
            '/collections/USCODE/search',
            params={
                'query': f'title:{title} AND section:{section}',
                'pageSize': 10
            }
        )
        
        if response:
            return response.json()
        return None
    
    def search_google_books(self, query: str) -> Optional[Dict[str, Any]]:
        """Search Google Books"""
        response = self.pool.get(
            'google_books',
            '/volumes',
            params={'q': query, 'maxResults': 5}
        )
        
        if response:
            return response.json()
        return None
    
    def close(self):
        """Close all connections"""
        self.pool.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()