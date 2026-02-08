---
title: "Missing Data Validation and Sanitization"
issue_id: "010"
priority: "P3"
status": "pending"
category: "data-quality"
severity: "medium"
created_at: "2026-01-16"
file: "lamda_scraper.py, models"
estimated_effort: "4 hours"
tags: ["validation", "data-quality", "pydantic"]
---

# ⚠️ Missing Data Validation and Sanitization

## Problem Statement

The code lacks comprehensive data validation, leading to:
- Invalid data stored in database
- Crashes when processing malformed data
- Security risks (XSS, injection attacks)
- Difficult to debug data quality issues

## Current Implementation Issues

### Issue 1: No Input Validation

**File**: `lamda_scraper.py:80-100`

```python
def parse_personal_homepage(self, url: str) -> dict:
    """Parse personal homepage"""
    # No URL validation
    resp = self.session.get(url, timeout=30)

    # No data validation
    return {
        'name_cn': raw_name,  # Could be None, empty, or malicious
        'email': raw_email,   # Not validated as email
        'github': raw_github  # Not validated as username
    }
```

**Risks**:
- Invalid URLs cause crashes
- Malformed data stored
- XSS vulnerabilities
- SQL injection (if using DB)

### Issue 2: No Type Safety

```python
# Candidate dataclass has no validation
@dataclass
class Candidate:
    name_cn: str  # Could be None!
    email: Optional[str] = None  # Not validated if present
    github: str = ""  # Could be invalid username
```

### Issue 3: No Data Sanitization

```python
# HTML not sanitized before storage
bio = soup.select_one('.bio').get_text()  # May contain scripts
candidate['bio'] = bio  # Stored as-is
```

## Impact Analysis

| Impact Area | Severity | Description |
|------------|----------|-------------|
| **Data Quality** | High | Invalid/corrupt data in outputs |
| **Security** | High | XSS, injection attacks |
| **Reliability** | High | Crashes on malformed input |
| **Debugging** | Medium | Hard to trace data quality issues |

## Proposed Solutions

### Solution 1: Use Pydantic for Validation (Recommended)

**Create `models.py`**:

```python
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
import re
from datetime import datetime

class GitHubUsername(str):
    """Validated GitHub username"""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('GitHub username must be a string')

        # GitHub username rules: max 39 chars, alphanumeric and hyphens
        # Cannot start or end with hyphen
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$'

        if not re.match(pattern, v):
            raise ValueError(f'Invalid GitHub username: {v}')

        return v

class CandidateModel(BaseModel):
    """Validated candidate model"""

    # Required fields
    name_cn: str = Field(..., min_length=1, max_length=100)
    source_type: str = Field(..., regex=r'^(alumni|phd)$')

    # Optional fields with validation
    name_en: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None  # Pydantic's built-in email validation
    phone: Optional[str] = None

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is None:
            return v

        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\.]', '', v)

        # Check if it looks like a phone number
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValueError(f'Invalid phone number: {v}')

        return v

    github: Optional[GitHubUsername] = None
    website: Optional[str] = None

    @validator('website')
    def validate_website(cls, v):
        """Validate URL format"""
        if v is None:
            return v

        from urllib.parse import urlparse

        try:
            result = urlparse(v)
            if not all([result.scheme, result.netloc]):
                raise ValueError
            return v
        except Exception:
            raise ValueError(f'Invalid URL: {v}')

    bio: Optional[str] = Field(None, max_length=5000)

    @validator('bio')
    def sanitize_bio(cls, v):
        """Sanitize bio to prevent XSS"""
        if v is None:
            return v

        import html

        # Escape HTML entities
        return html.escape(v)

    # Education
    education: Optional[List[dict]] = None

    @validator('education')
    def validate_education(cls, v):
        """Validate education list"""
        if v is None:
            return v

        if not isinstance(v, list):
            raise ValueError('Education must be a list')

        for edu in v:
            if not isinstance(edu, dict):
                raise ValueError('Each education entry must be a dict')

            # Validate required fields
            if 'school' not in edu:
                raise ValueError('Education entry missing "school" field')

        return v

    # Publications
    publications: Optional[List[dict]] = None

    @validator('publications')
    def validate_publications(cls, v):
        """Validate publications list"""
        if v is None:
            return v

        if not isinstance(v, list):
            raise ValueError('Publications must be a list')

        for pub in v:
            if not isinstance(pub, dict):
                raise ValueError('Each publication must be a dict')

        return v

    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.now)
    data_source: str = Field(..., min_length=1)

    class Config:
        """Pydantic config"""
        # Strip whitespace from strings
        anystr_strip_whitespace = True
        # Prevent extra fields
        extra = 'forbid'

# Usage
try:
    candidate = CandidateModel(
        name_cn="张三",
        email="zhangsan@example.com",  # Validated
        github="zhang-san",  # Validated
        website="https://example.com",  # Validated
        bio="<script>alert('xss')</script>",  # Will be escaped
        source_type="alumni",
        data_source="lamda_nju"
    )

    print(candidate.dict())

except ValidationError as e:
    print(f"Validation error: {e}")
```

### Solution 2: URL Validation

```python
from urllib.parse import urlparse
from typing import Optional

def validate_url(url: str, allowed_schemes: Optional[list] = None) -> bool:
    """
    Validate URL format and scheme

    Args:
        url: URL to validate
        allowed_schemes: List of allowed schemes (default: ['http', 'https'])

    Returns:
        True if valid

    Raises:
        ValueError: If invalid
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    try:
        result = urlparse(url)

        # Check scheme
        if result.scheme not in allowed_schemes:
            raise ValueError(f"Invalid URL scheme: {result.scheme}")

        # Check network location
        if not result.netloc:
            raise ValueError("URL missing network location")

        # Check for valid domain
        if '.' not in result.netloc:
            raise ValueError("Invalid domain name")

        return True

    except Exception as e:
        raise ValueError(f"Invalid URL '{url}': {e}")

# Usage
try:
    validate_url("https://www.lamda.nju.edu.cn")
    print("✅ Valid URL")
except ValueError as e:
    print(f"❌ {e}")
```

### Solution 3: Email Validation

```python
import re
from typing import Optional

def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        True if valid

    Raises:
        ValueError: If invalid
    """
    if not email:
        raise ValueError("Email cannot be empty")

    # Basic email regex (RFC 5322 compliant)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")

    return True

# Or use Pydantic's EmailStr (recommended)
from pydantic import BaseModel, EmailStr

class ContactInfo(BaseModel):
    email: EmailStr  # Automatically validated

# Usage
try:
    validate_email("user@example.com")
    print("✅ Valid email")
except ValueError as e:
    print(f"❌ {e}")
```

### Solution 4: Sanitize HTML Input

```python
import html
from bs4 import BeautifulSoup

def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks

    Args:
        html_content: Raw HTML content

    Returns:
        Sanitized text (stripped of HTML tags)
    """
    if not html_content:
        return ""

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Get text only (removes all tags)
    text = soup.get_text(separator=' ', strip=True)

    # Escape any remaining HTML entities
    return html.escape(text)

# Alternative: Allow certain safe tags
def sanitize_html_safe(html_content: str, allowed_tags: Optional[list] = None) -> str:
    """
    Sanitize HTML but keep certain safe tags

    Args:
        html_content: Raw HTML content
        allowed_tags: List of allowed tags (default: ['p', 'br', 'b', 'i'])

    Returns:
        Sanitized HTML with safe tags preserved
    """
    if allowed_tags is None:
        allowed_tags = ['p', 'br', 'b', 'i', 'strong', 'em']

    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove disallowed tags
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()

    # Remove dangerous attributes
    for tag in soup.find_all(True):
        tag.attrs = {k: v for k, v in tag.attrs.items()
                    if k in ['href', 'src', 'alt', 'title']}

    return str(soup)

# Usage
safe_bio = sanitize_html("<script>alert('xss')</script><p>Hello</p>")
# Result: "Hello"

safe_bio_partial = sanitize_html_safe("<p>Hello</p><script>alert('xss')</script>")
# Result: "<p>Hello</p>alert('xss')"
```

### Solution 5: Validate Before Processing

```python
from lamda_scraper.models import CandidateModel

def parse_personal_homepage(self, url: str) -> dict:
    """Parse personal homepage with validation"""
    try:
        # Validate URL first
        validate_url(url)

        # Fetch page
        resp = self.session.get(url, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract data
        raw_data = {
            'name_cn': self._extract_name_cn(soup),
            'email': self._extract_email(soup),
            'github': self._extract_github(soup),
            'website': url,
            'bio': self._extract_bio(soup),
            'source_type': 'alumni',
            'data_source': 'lamda_nju'
        }

        # Validate and sanitize using Pydantic
        candidate = CandidateModel(**raw_data)

        # Return validated data as dict
        return candidate.dict()

    except ValueError as e:
        logger.error(f"Validation error for {url}: {e}")
        return {}

    except Exception as e:
        logger.error(f"Error parsing {url}: {e}")
        return {}
```

## Testing Strategy

### Test Validation

```python
import pytest
from pydantic import ValidationError
from lamda_scraper.models import CandidateModel

def test_valid_candidate():
    """Test valid candidate creation"""
    candidate = CandidateModel(
        name_cn="张三",
        email="test@example.com",
        github="validuser",
        source_type="alumni",
        data_source="lamda_nju"
    )

    assert candidate.name_cn == "张三"
    assert candidate.email == "test@example.com"

def test_invalid_email():
    """Test email validation"""
    with pytest.raises(ValidationError):
        CandidateModel(
            name_cn="张三",
            email="not-an-email",  # Invalid
            source_type="alumni",
            data_source="lamda_nju"
        )

def test_invalid_github_username():
    """Test GitHub username validation"""
    with pytest.raises(ValidationError):
        CandidateModel(
            name_cn="张三",
            github="-invalid",  # Cannot start with hyphen
            source_type="alumni",
            data_source="lamda_nju"
        )

def test_xss_sanitization():
    """Test XSS prevention"""
    candidate = CandidateModel(
        name_cn="张三",
        bio="<script>alert('xss')</script>Hello",
        source_type="alumni",
        data_source="lamda_nju"
    )

    # Script tags should be escaped
    assert "<script>" not in candidate.bio
    assert "Hello" in candidate.bio
```

## Recommended Action Plan

1. **Week 1**:
   - [ ] Create Pydantic models
   - [ ] Add validators for all fields
   - [ ] Add sanitization functions
   - [ ] Write validation tests

2. **Week 2**:
   - [ ] Update scraper to use models
   - [ ] Add validation at entry points
   - [ ] Add sanitization for all user input
   - [ ] Test with edge cases

## Benefits

| Benefit | Impact |
|---------|--------|
| **Data quality** | Only valid data stored |
| **Security** | XSS/injection prevention |
| **Reliability** | Fail fast on invalid input |
| **Debugging** | Clear error messages |

## Related Issues

- Issue #001: SSL Verification
- Issue #005: Error Handling

## References

- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)

---

**Assigned To**: TBD
**Due Date**: 2026-02-13 (Lower Priority)
**Dependencies**: None
