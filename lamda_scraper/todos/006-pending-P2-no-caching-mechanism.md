---
title: "No Caching Mechanism for API Calls"
issue_id: "006"
priority: "P2"
status: "pending"
category: "performance"
severity: "medium"
created_at: "2026-01-16"
file: "github_enricher.py, scrape_websites_for_contacts.py"
lines: "multiple"
estimated_effort: "4 hours"
tags: ["performance", "caching", "api-optimization"]
---

# ⚠️ No Caching Mechanism for API Calls

## Problem Statement

Every run makes fresh API calls to GitHub and scrapes websites without any caching mechanism. This results in:
- Wasted API quota (GitHub 5000/hour limit)
- Slower execution times
- Unnecessary load on external servers
- Higher costs if using paid APIs

## Current Implementation Issues

### Issue 1: No GitHub API Caching

**File**: `github_enricher.py:60-80`

```python
def get_user_info(self, username: str) -> dict:
    """Get user info from GitHub API"""
    url = f"https://api.github.com/users/{username}"
    resp = self.session.get(url, timeout=30)
    return resp.json()

# Every call hits the API, even if we just fetched this user
```

**Impact**:
- Repeated runs fetch same data repeatedly
- Wastes GitHub API quota
- Slower execution (~500ms per call)

### Issue 2: No Web Scraping Caching

**File**: `scrape_websites_for_contacts.py:40-60`

```python
def scrape_website(self, website_url: str) -> dict:
    """Scrape website for contact info"""
    resp = self.session.get(website_url, timeout=30, verify=False)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # ... parsing logic

# Scrape same websites repeatedly
```

**Impact**:
- Repeated scraping of same URLs
- Unnecessary load on external servers
- Slower execution

### Issue 3: No Result Persistence

Intermediate results are not cached between runs:
- If script crashes, all progress is lost
- Cannot resume from last successful state
- Must re-scrape everything on re-run

## Performance Impact

| Metric | Without Caching | With Caching | Improvement |
|--------|----------------|--------------|-------------|
| **API calls** | 500 calls/run | 100 calls/run (first run) | **5x fewer** |
| **Execution time** | ~5 minutes | ~1 minute (subsequent) | **5x faster** |
| **API quota** | 500/hour | 100/hour | **Save 400 calls** |
| **Server load** | High | Low | **Reduced** |

## Proposed Solutions

### Solution 1: File-Based Cache with TTL (Recommended)

Create `cache.py`:

```python
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
import pickle

class FileCache:
    """File-based cache with TTL support"""

    def __init__(self, cache_dir: str = "./cache", default_ttl: int = 3600):
        """
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key"""
        # Use hash to avoid invalid filenames
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def _is_expired(self, cache_path: Path, ttl: int) -> bool:
        """Check if cache file is expired"""
        if not cache_path.exists():
            return True

        # Check age
        file_mtime = cache_path.stat().st_mtime
        age = time.time() - file_mtime

        return age > ttl

    def get(self, key: str, ttl: Optional[int] = None) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            ttl: Time-to-live in seconds (uses default if not specified)

        Returns:
            Cached value or None if not found/expired
        """
        ttl = ttl or self.default_ttl
        cache_path = self._get_cache_path(key)

        # Check if expired
        if self._is_expired(cache_path, ttl):
            return None

        # Load from cache
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)

            logger.debug(f"Cache hit: {key}")
            return data['value']

        except (pickle.PickleError, EOFError, json.JSONDecodeError) as e:
            logger.warning(f"Cache corruption for {key}: {e}")
            # Delete corrupted cache
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: Any):
        """Set value in cache"""
        cache_path = self._get_cache_path(key)

        data = {
            'value': value,
            'cached_at': datetime.now().isoformat()
        }

        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)

        logger.debug(f"Cache set: {key}")

    def delete(self, key: str):
        """Delete cache entry"""
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)

    def clear(self):
        """Clear all cache"""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
        logger.info("Cache cleared")

    def stats(self) -> dict:
        """Get cache statistics"""
        cache_files = list(self.cache_dir.glob("*.cache"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            'entries': len(cache_files),
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }
```

### Solution 2: Cached GitHub Enricher

```python
from lamda_scraper.cache import FileCache

class CachedGitHubEnricher(GitHubEnricher):
    """GitHub enricher with caching"""

    # Cache TTLs (in seconds)
    USER_INFO_TTL = 7 * 24 * 3600      # 7 days - user info rarely changes
    REPOS_TTL = 1 * 24 * 3600          # 1 day - repos may update daily
    ACTIVITY_TTL = 6 * 3600            # 6 hours - activity changes often

    def __init__(self, token: str = None, cache_dir: str = "./cache/github"):
        super().__init__(token)
        self.cache = FileCache(cache_dir=cache_dir)

    def get_user_info(self, username: str) -> dict:
        """Get user info with caching"""
        cache_key = f"user:{username}"

        # Try cache first
        cached = self.cache.get(cache_key, ttl=self.USER_INFO_TTL)
        if cached:
            logger.info(f"Cache hit for user: {username}")
            return cached

        # Cache miss - fetch from API
        logger.info(f"Cache miss for user: {username}")
        user_info = super().get_user_info(username)

        # Store in cache
        self.cache.set(cache_key, user_info)

        return user_info

    def get_user_repos(self, username: str) -> list:
        """Get user repos with caching"""
        cache_key = f"repos:{username}"

        cached = self.cache.get(cache_key, ttl=self.REPOS_TTL)
        if cached:
            return cached

        repos = super().get_user_repos(username)
        self.cache.set(cache_key, repos)

        return repos

    def clear_cache(self):
        """Clear GitHub cache"""
        self.cache.clear()
```

### Solution 3: Cached Website Scraper

```python
class CachedWebsiteScraper:
    """Website scraper with caching"""

    # Cache TTLs
    WEBSITE_TTL = 30 * 24 * 3600  # 30 days - contact info rarely changes

    def __init__(self, cache_dir: str = "./cache/websites"):
        self.cache = FileCache(cache_dir=cache_dir)
        self.session = requests.Session()

    def scrape_website(self, url: str) -> dict:
        """Scrape website with caching"""
        cache_key = f"website:{url}"

        # Try cache
        cached = self.cache.get(cache_key, ttl=self.WEBSITE_TTL)
        if cached:
            logger.info(f"Cache hit for website: {url}")
            return cached

        # Cache miss - scrape
        logger.info(f"Cache miss for website: {url}")
        data = self._scrape_impl(url)

        # Store in cache
        self.cache.set(cache_key, data)

        return data

    def _scrape_impl(self, url: str) -> dict:
        """Actual scraping implementation"""
        resp = self.session.get(url, timeout=30, verify=True)
        soup = BeautifulSoup(resp.text, 'html.parser')

        return {
            'email': self._extract_email(soup),
            'phone': self._extract_phone(soup),
            'bio': self._extract_bio(soup)
        }
```

### Solution 4: In-Memory Cache with Requests Cache

For simpler use cases, use `requests-cache` library:

```python
import requests_cache

# Install: pip install requests-cache

# Setup cache
requests_cache.install_cache(
    cache_name='github_api',
    backend='sqlite',
    expire_after=timedelta(hours=1)
)

# All requests are now cached automatically
response = requests.get('https://api.github.com/users/octocat')
# First call: hits API
# Second call: returns cached response

# Clear cache if needed
requests_cache.clear()
```

### Solution 5: Checkpoint/Resume Support

```python
class CheckpointManager:
    """Manage checkpoints for resumable execution"""

    def __init__(self, checkpoint_file: str = "./checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)

    def load(self) -> dict:
        """Load checkpoint state"""
        if not self.checkpoint_file.exists():
            return {}

        with open(self.checkpoint_file) as f:
            return json.load(f)

    def save(self, state: dict):
        """Save checkpoint state"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(state, f, indent=2)

    def clear(self):
        """Clear checkpoint"""
        self.checkpoint_file.unlink(missing_ok=True)

# Usage in scraper
class LAMDAScraper:
    def run_with_resume(self):
        """Run with checkpoint/resume support"""
        checkpoint_mgr = CheckpointManager()

        # Load previous state
        state = checkpoint_mgr.load()
        last_index = state.get('last_index', 0)

        logger.info(f"Resuming from index {last_index}")

        candidates = self.get_candidates()

        # Process from last checkpoint
        for idx, candidate in enumerate(candidates[last_index:], start=last_index):
            try:
                self.process_candidate(candidate)

                # Save checkpoint every 10 candidates
                if idx % 10 == 0:
                    checkpoint_mgr.save({'last_index': idx})
                    logger.info(f"Checkpoint saved at index {idx}")

            except Exception as e:
                logger.error(f"Error processing {candidate.name}: {e}")
                # Save checkpoint before exiting
                checkpoint_mgr.save({'last_index': idx})
                raise

        # Clear checkpoint on success
        checkpoint_mgr.clear()
```

## Recommended Action Plan

1. **Phase 1** (Week 1):
   - [ ] Implement `FileCache` class
   - [ ] Add TTL support
   - [ ] Add cache statistics
   - [ ] Write unit tests for cache

2. **Phase 2** (Week 2):
   - [ ] Create `CachedGitHubEnricher`
   - [ ] Add caching to all GitHub API calls
   - [ ] Set appropriate TTLs for different data types
   - [ ] Test cache hit/miss behavior

3. **Phase 3** (Week 3):
   - [ ] Add website scraping cache
   - [ ] Implement checkpoint/resume support
   - [ ] Add cache management commands (clear, stats)
   - [ ] Update documentation

## Cache TTL Recommendations

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| **GitHub user info** | 7 days | Rarely changes |
| **GitHub repos** | 1 day | May update daily |
| **GitHub activity** | 6 hours | Changes often |
| **Website contact info** | 30 days | Rarely changes |
| **Parsed page data** | 7 days | Content changes slowly |
| **RSS feed data** | 1 hour | Updates frequently |

## Testing Strategy

### Test Cache Hit

```python
def test_cache_hit():
    """Test cache returns cached value"""
    cache = FileCache()
    cache.set("test_key", {"data": "value"})

    result = cache.get("test_key")

    assert result == {"data": "value"}

def test_cache_miss():
    """Test cache returns None for missing/expired"""
    cache = FileCache()

    result = cache.get("nonexistent")

    assert result is None
```

### Test TTL Expiration

```python
def test_cache_expiration():
    """Test cache expires after TTL"""
    cache = FileCache(default_ttl=1)  # 1 second TTL
    cache.set("test_key", {"data": "value"})

    # Should be cached immediately
    assert cache.get("test_key") is not None

    # Wait for expiration
    time.sleep(2)

    # Should be expired
    assert cache.get("test_key") is None
```

### Test Cached Enricher

```python
def test_github_enricher_cache():
    """Test GitHub enricher uses cache"""
    enricher = CachedGitHubEnricher()

    # First call - cache miss
    user1 = enricher.get_user_info("octocac")
    assert mock_api.call_count == 1

    # Second call - cache hit
    user2 = enricher.get_user_info("octocat")
    assert mock_api.call_count == 1  # No additional call

    assert user1 == user2
```

## Cache Management CLI

```python
import click

@click.group()
def cache():
    """Cache management commands"""
    pass

@cache.command()
@click.option('--cache-dir', default='./cache')
def stats(cache_dir):
    """Show cache statistics"""
    cache = FileCache(cache_dir=cache_dir)
    stats = cache.stats()

    click.echo(f"Cache directory: {stats['cache_dir']}")
    click.echo(f"Entries: {stats['entries']}")
    click.echo(f"Total size: {stats['total_size_mb']:.2f} MB")

@cache.command()
@click.option('--cache-dir', default='./cache')
@click.confirmation_option(prompt='Clear all cache?')
def clear(cache_dir):
    """Clear all cache"""
    cache = FileCache(cache_dir=cache_dir)
    cache.clear()
    click.echo("Cache cleared")

# Usage
# python lamda_scraper.py cache stats
# python lamda_scraper.py cache clear
```

## Benefits

| Benefit | Impact |
|---------|--------|
| **Faster execution** | 5x speedup on subsequent runs |
| **API quota savings** | Save 400+ calls/hour |
| **Lower costs** | If using paid APIs |
| **Better UX** | Resume from checkpoints |
| **Reduced load** | On external servers |

## Related Issues

- Issue #002: GitHub Token Management
- Issue #009: Performance Optimization Needed
- Issue #007: Serial Processing Bottleneck

## References

- [requests-cache Documentation](https://requests-cache.readthedocs.io/)
- [Caching Best Practices](https://docs.python.org/3/library/cache.html)
- [GitHub API Best Practices](https://docs.github.com/en/rest/guides/best-practices-for-integrators)

---

**Assigned To**: TBD
**Due Date**: 2026-02-06 (Medium Priority)
**Dependencies**: None
