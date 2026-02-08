---
title: "Inconsistent Error Handling - Broad Exception Catches"
issue_id: "005"
priority: "P2"
status: "pending"
category: "code-quality"
severity: "medium"
created_at: "2026-01-16"
file: "lamda_scraper.py, github_enricher.py"
lines: "multiple"
estimated_effort: "3 hours"
tags: ["error-handling", "exception-handling", "reliability"]
---

# ⚠️ Inconsistent Error Handling - Broad Exception Catches

## Problem Statement

The codebase uses broad `except Exception` statements that catch all exceptions, making it difficult to:
- Handle specific errors appropriately
- Debug issues when they occur
- Implement proper retry logic
- Provide meaningful error messages to users

## Current Implementation Issues

### Issue 1: Broad Exception Catches

**File**: `lamda_scraper.py:150-160`

```python
def parse_personal_homepage(self, url: str) -> dict:
    try:
        # Parsing logic
        resp = self.session.get(url, timeout=30)
        # ... more code
    except Exception as e:
        logger.error(f"Error parsing {url}: {e}")
        return {}  # Returns empty dict for ALL errors
```

**Problems**:
- Catches ALL exceptions (KeyboardInterrupt, SystemExit, etc.)
- No differentiation between network errors, parsing errors, etc.
- Returns empty dict, hiding the real issue
- No retry logic for transient failures

### Issue 2: No Error Propagation

**File**: `github_enricher.py:80-90`

```python
def get_user_info(self, username: str) -> dict:
    try:
        resp = self.session.get(f"https://api.github.com/users/{username}")
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        return None  # Silent failure
```

**Problems**:
- Calling code doesn't know if user not found vs network error
- No way to handle 404 (user doesn't exist) vs 500 (server error)
- Silent failure makes debugging difficult

### Issue 3: No Custom Exceptions

The codebase has no custom exceptions, making it hard to:
- Distinguish between different error types
- Handle errors appropriately at different layers
- Provide meaningful error messages

## Impact Analysis

| Impact Area | Severity | Description |
|------------|----------|-------------|
| **Debugging** | High | Cannot identify root cause of failures |
| **Reliability** | High | Silent failures hide real issues |
| **User Experience** | Medium | Generic error messages |
| **Monitoring** | High | Cannot track specific error types |
| **Retry Logic** | High | Cannot retry only transient errors |

## Proposed Solutions

### Solution 1: Define Custom Exceptions (Recommended)

Create `exceptions.py`:

```python
"""Custom exceptions for lamda_scraper"""

class LAMDAScraperError(Exception):
    """Base exception for all scraper errors"""
    pass

# Network errors
class NetworkError(LAMDAScraperError):
    """Network-related errors (timeout, connection refused, etc.)"""
    pass

class TimeoutError(NetworkError):
    """Request timeout"""
    pass

class ConnectionError(NetworkError):
    """Connection failed"""
    pass

# Parsing errors
class ParseError(LAMDAScraperError):
    """HTML/XML parsing errors"""
    pass

class MissingDataError(ParseError):
    """Expected data not found on page"""
    pass

# API errors
class APIError(LAMDAScraperError):
    """API-related errors"""
    pass

class RateLimitError(APIError):
    """Rate limit exceeded"""
    pass

class AuthenticationError(APIError):
    """Authentication failed"""
    pass

class NotFoundError(APIError):
    """Resource not found (404)"""
    pass

class ServerError(APIError):
    """Server error (5xx)"""
    pass

# Configuration errors
class ConfigurationError(LAMDAScraperError):
    """Configuration-related errors"""
    pass

# Validation errors
class ValidationError(LAMDAScraperError):
    """Data validation errors"""
    pass
```

### Solution 2: Specific Exception Handling

**Before** (broad catch):

```python
def parse_personal_homepage(self, url: str) -> dict:
    try:
        resp = self.session.get(url, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # ... parsing logic
    except Exception as e:
        logger.error(f"Error: {e}")
        return {}
```

**After** (specific handling):

```python
from requests.exceptions import RequestException, Timeout, ConnectionError
from lamda_scraper.exceptions import (
    NetworkError, ParseError, MissingDataError
)

def parse_personal_homepage(self, url: str) -> dict:
    """Parse personal homepage with specific error handling"""
    try:
        # Fetch page
        resp = self._fetch_page(url)

    except Timeout as e:
        logger.warning(f"Timeout fetching {url}: {e}")
        raise TimeoutError(f"Request timeout for {url}") from e

    except ConnectionError as e:
        logger.error(f"Connection error for {url}: {e}")
        raise NetworkError(f"Cannot connect to {url}") from e

    except RequestException as e:
        logger.error(f"Network error for {url}: {e}")
        raise NetworkError(f"Network error: {e}") from e

    try:
        # Parse page
        return self._parse_page(resp.text)

    except ParseError as e:
        logger.warning(f"Parse error for {url}: {e}")
        # Return partial data if possible
        return self._get_partial_data(resp.text)

    except MissingDataError as e:
        logger.info(f"Missing expected data on {url}: {e}")
        # Some fields missing is OK, return what we have
        return self._get_available_data(resp.text)
```

### Solution 3: Retry Logic for Transient Errors

```python
from functools import wraps
import time
from lamda_scraper.exceptions import NetworkError, TimeoutError

def retry_on_transient_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry on transient errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)

                except (TimeoutError, ConnectionError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Max retries exceeded: {e}")

            raise last_exception

        return wrapper
    return decorator

# Usage
class LAMDAScraper:
    @retry_on_transient_error(max_retries=3, delay=1.0)
    def fetch_page(self, url: str) -> requests.Response:
        """Fetch page with retry logic"""
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp
```

### Solution 4: Proper Error Propagation

**Before** (silent failure):

```python
def get_user_info(self, username: str) -> dict:
    try:
        resp = self.session.get(f"https://api.github.com/users/{username}")
        return resp.json()
    except Exception as e:
        logger.error(f"Failed: {e}")
        return None
```

**After** (proper propagation):

```python
from lamda_scraper.exceptions import NotFoundError, ServerError

def get_user_info(self, username: str) -> dict:
    """Get user info with proper error handling"""
    try:
        resp = self.session.get(f"https://api.github.com/users/{username}")
        resp.raise_for_status()  # Raises HTTPError for 4xx/5xx

        return resp.json()

    except requests.HTTPError as e:
        status_code = resp.status_code

        if status_code == 404:
            logger.info(f"User not found: {username}")
            raise NotFoundError(f"GitHub user '{username}' not found") from e

        elif status_code == 403:
            logger.error(f"Rate limit exceeded")
            raise RateLimitError("GitHub API rate limit exceeded") from e

        elif 500 <= status_code < 600:
            logger.error(f"GitHub server error: {status_code}")
            raise ServerError(f"GitHub API server error: {status_code}") from e

        else:
            logger.error(f"Unexpected HTTP error: {status_code}")
            raise APIError(f"HTTP error {status_code}") from e
```

### Solution 5: Error Context and Recovery

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class ErrorContext:
    """Context information for errors"""
    url: str
    username: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'username': self.username,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'metadata': self.metadata or {}
        }

class LAMDAScraper:
    def parse_with_recovery(self, url: str) -> dict:
        """Parse with graceful degradation"""
        context = ErrorContext(url=url)

        try:
            return self._parse_full(url)

        except ParseError as e:
            # Try partial recovery
            logger.warning(f"Full parse failed, trying partial: {e}")
            try:
                return self._parse_partial(url)
            except Exception as e2:
                # Last resort: minimal data
                logger.error(f"Partial parse failed: {e2}")
                return self._parse_minimal(url)

        except NetworkError as e:
            # Cannot recover from network errors
            context.metadata = {'error_type': 'network', 'recoverable': False}
            logger.error(f"Unrecoverable network error: {e}")
            raise
```

## Recommended Action Plan

1. **Phase 1** (Week 1):
   - [ ] Create `exceptions.py` with custom exceptions
   - [ ] Add exception hierarchy (network, parse, API, config)
   - [ ] Document when to use each exception
   - [ ] Add unit tests for exception raising

2. **Phase 2** (Week 2):
   - [ ] Replace broad `except Exception` with specific exceptions
   - [ ] Start with critical paths (HTTP requests, parsing)
   - [ ] Add proper error logging with context
   - [ ] Test error scenarios

3. **Phase 3** (Week 3):
   - [ ] Implement retry logic for transient errors
   - [ ] Add error recovery mechanisms
   - [ ] Update error messages to be user-friendly
   - [ ] Add integration tests for error handling

## Error Handling Best Practices

### DO ✅

```python
# Specific exception handling
try:
    result = api_call()
except TimeoutError as e:
    logger.warning(f"Timeout: {e}")
    # Retry logic
except AuthenticationError as e:
    logger.error(f"Auth failed: {e}")
    # Don't retry auth errors
    raise

# Provide context
except NetworkError as e:
    logger.error(f"Failed to fetch {url}: {e}")
    raise

# Graceful degradation
try:
    return full_parse()
except ParseError:
    return partial_parse()
```

### DON'T ❌

```python
# Broad exception catch
try:
    result = api_call()
except Exception as e:
    logger.error(f"Error: {e}")
    return None  # Silent failure

# Swallowing exceptions
try:
    result = api_call()
except:
    pass  # Never do this!

# No error propagation
try:
    result = api_call()
except Exception as e:
    logger.error(f"Error: {e}")
    return {}  # Caller doesn't know what went wrong
```

## Testing Strategy

### Test Specific Exceptions

```python
def test_timeout_error():
    """Test timeout error handling"""
    scraper = LAMDAScraper()

    with patch.object(scraper.session, 'get', side_effect=TimeoutError):
        with pytest.raises(TimeoutError):
            scraper.fetch_page("http://example.com")

def test_not_found_error():
    """Test 404 error handling"""
    enricher = GitHubEnricher()

    with pytest.raises(NotFoundError) as exc_info:
        enricher.get_user_info("nonexistent-user")

    assert "not found" in str(exc_info.value).lower()
```

### Test Retry Logic

```python
def test_retry_on_timeout():
    """Test retry logic"""
    scraper = LAMDAScraper()

    # Fail twice, then succeed
    with patch.object(scraper.session, 'get') as mock_get:
        mock_get.side_effect = [
            TimeoutError,
            TimeoutError,
            Mock(status_code=200, text="<html></html>")
        ]

        result = scraper.fetch_page("http://example.com")

        assert mock_get.call_count == 3
```

## Error Handling Checklist

- [ ] Define custom exception hierarchy
- [ ] Replace all `except Exception` with specific exceptions
- [ ] Add retry logic for transient errors
- [ ] Implement proper error propagation
- [ ] Add error context (URL, username, etc.)
- [ ] Update error messages to be meaningful
- [ ] Add unit tests for error scenarios
- [ ] Add integration tests for error recovery

## Related Issues

- Issue #001: SSL Verification Disabled
- Issue #002: GitHub Token Management
- Issue #008: Missing Unit Tests

## References

- [Python Exception Handling Best Practices](https://docs.python.org/3/tutorial/errors.html)
- [Google Python Style Guide: Exceptions](https://google.github.io/styleguide/pyguide.html#Exceptions)
- [The Missing README: Error Handling](https://github.com/LappleApple/missing-readmes/blob/master/content/error-handling.md)

---

**Assigned To**: TBD
**Due Date**: 2026-02-06 (Medium Priority)
**Dependencies**: None
