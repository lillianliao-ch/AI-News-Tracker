---
title: "GitHub Token Management - Security & Rate Limiting Issues"
issue_id: "002"
priority: "P1"
status: "pending"
category: "security"
severity: "high"
created_at: "2026-01-16"
file: "github_enricher.py"
lines: "45-50"
estimated_effort: "1 hour"
tags: ["security", "github", "api", "authentication"]
---

# 🔴 GitHub Token Management - Security & Rate Limiting Issues

## Problem Statement

GitHub API tokens are stored in plain text without proper encryption, access controls, or rotation mechanisms. Additionally, there's no robust rate limiting handling despite GitHub's 5000 requests/hour limit.

## Current Implementation

**File**: `github_enricher.py:45-50`

```python
class GitHubEnricher:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token is required")
```

## Security & Operational Risks

1. **Token Exposure**: Plain text storage in environment variables
2. **No Token Rotation**: Tokens never expire, increasing compromise risk
3. **No Rate Limit Tracking**: Could hit GitHub API limits unexpectedly
4. **No Fallback Mechanism**: Single token failure = complete failure
5. **Logging Issues**: Tokens might be accidentally logged

## Root Causes

- Using basic environment variable approach
- No token lifecycle management
- Missing rate limit monitoring
- No token validation on startup

## Proposed Solutions

### Solution 1: Implement Token Management Class (Recommended)

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import os

@dataclass
class GitHubTokenConfig:
    """GitHub token configuration with lifecycle management"""
    token: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_rotated: datetime = None
    request_count: int = 0
    rate_limit_reset: Optional[datetime] = None
    remaining_requests: int = 5000

    @classmethod
    def from_env(cls, env_var: str = "GITHUB_TOKEN") -> "GitHubTokenConfig":
        """Load token from environment with metadata"""
        token = os.getenv(env_var)
        if not token:
            raise ValueError(f"{env_var} not found in environment")

        # Hash token for logging (never log actual token)
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]

        return cls(
            token=token,
            created_at=datetime.now(),
            last_rotated=datetime.now()
        )

    def get_safe_identifier(self) -> str:
        """Get safe token identifier for logging"""
        return f"gh_{self.token[:8]}...{self.token[-4:]}"

    def is_expired(self) -> bool:
        """Check if token needs rotation"""
        if not self.expires_at:
            return False
        return datetime.now() >= self.expires_at

class GitHubEnricher:
    def __init__(self, token_config: GitHubTokenConfig = None):
        self.token_config = token_config or GitHubTokenConfig.from_env()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token_config.token}",
            "Accept": "application/vnd.github.v3+json"
        })

        # Validate token on startup
        self._validate_token()

    def _validate_token(self):
        """Validate token and check rate limits"""
        resp = self.session.get("https://api.github.com/rate_limit")
        if resp.status_code != 200:
            raise ValueError(f"Invalid GitHub token: {resp.status_code}")

        rate_info = resp.json()["resources"]["core"]
        self.token_config.remaining_requests = rate_info["remaining"]
        reset_timestamp = rate_info["reset"]
        self.token_config.rate_limit_reset = datetime.fromtimestamp(reset_timestamp)

        logger.info(f"GitHub token {self.token_config.get_safe_identifier()} validated: "
                   f"{self.token_config.remaining_requests} requests remaining")

    def _check_rate_limit(self):
        """Check rate limit before making request"""
        if self.token_config.remaining_requests <= 10:
            reset_time = self.token_config.rate_limit_reset
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            logger.warning(f"Rate limit almost reached. Waiting {wait_seconds:.0f}s")
            time.sleep(wait_seconds)
            self._validate_token()  # Refresh counters

    def _make_request(self, url: str) -> dict:
        """Make request with rate limit tracking"""
        self._check_rate_limit()

        resp = self.session.get(url, timeout=30)
        self.token_config.request_count += 1

        # Update remaining from headers
        remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
        self.token_config.remaining_requests = remaining

        if resp.status_code == 403:
            logger.error(f"Rate limit exceeded for {self.token_config.get_safe_identifier()}")
            raise Exception("GitHub API rate limit exceeded")

        return resp.json()

    def get_user_info(self, username: str) -> dict:
        """Get user info with rate limit protection"""
        return self._make_request(f"https://api.github.com/users/{username}")
```

### Solution 2: Multi-Token Support with Fallback

```python
class MultiTokenGitHubEnricher:
    """Support multiple GitHub tokens with automatic failover"""

    def __init__(self, tokens: List[str]):
        self.token_configs = [GitHubTokenConfig.from_token(t) for t in tokens]
        self.current_index = 0

    def get_active_config(self) -> GitHubTokenConfig:
        """Get current active token config"""
        return self.token_configs[self.current_index]

    def rotate_token(self):
        """Rotate to next available token"""
        self.current_index = (self.current_index + 1) % len(self.token_configs)
        logger.info(f"Rotated to token {self.get_active_config().get_safe_identifier()}")
```

### Solution 3: Secure Token Storage with Encryption

```python
from cryptography.fernet import Fernet
import base64

class SecureTokenStorage:
    """Encrypt tokens at rest"""

    def __init__(self, encryption_key: str = None):
        # Load from environment or generate
        key = encryption_key or os.getenv("TOKEN_ENCRYPTION_KEY")
        if not key:
            raise ValueError("TOKEN_ENCRYPTION_KEY required")
        self.cipher = Fernet(key.encode())

    def encrypt_token(self, token: str) -> str:
        """Encrypt token for storage"""
        return self.cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted: str) -> str:
        """Decrypt token for use"""
        return self.cipher.decrypt(encrypted.encode()).decode()
```

## Recommended Action Plan

1. **Immediate** (Week 1):
   - [ ] Implement `GitHubTokenConfig` class
   - [ ] Add token validation on startup
   - [ ] Add rate limit tracking
   - [ ] Implement safe token logging (hash-based)

2. **Short-term** (Week 2):
   - [ ] Add multi-token support
   - [ ] Implement automatic token rotation
   - [ ] Add rate limit wait/retry logic
   - [ ] Create token rotation script

3. **Long-term** (Month 1):
   - [ ] Implement encrypted token storage
   - [ ] Set up automated token rotation (cron job)
   - [ ] Add monitoring and alerts for token issues
   - [ ] Document token lifecycle management

## Environment Variables Required

```bash
# Primary token
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Backup tokens (optional, for failover)
GITHUB_TOKEN_2=ghp_yyyyyyyyyyyyyyyyyyyy
GITHUB_TOKEN_3=ghp_zzzzzzzzzzzzzzzzzzzz

# Encryption key (for token storage)
TOKEN_ENCRYPTION_KEY=<base64-encoded-key>
```

## Testing Checklist

- [ ] Test token validation on startup
- [ ] Test rate limit tracking accuracy
- [ ] Test token rotation when limit reached
- [ ] Test multi-token failover
- [ ] Test encrypted storage (encrypt/decrypt cycle)
- [ ] Test logging doesn't expose actual tokens
- [ ] Load test with multiple tokens

## Security Considerations

- **Never log actual tokens**: Always use safe identifiers or hashes
- **Rotate tokens regularly**: Every 90 days recommended
- **Use least privilege**: Token should only need `public_repo` scope
- **Monitor usage**: Set up alerts for unusual token activity
- **Secure storage**: Use encrypted storage for tokens at rest

## Related Issues

- Issue #001: SSL Verification Disabled
- Issue #007: No Caching for API Calls

## References

- [GitHub API: Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [GitHub: Best Practices for Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [OWASP: Key Management](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)

---

**Assigned To**: TBD
**Due Date**: 2026-01-23 (High Priority)
**Dependencies**: None
