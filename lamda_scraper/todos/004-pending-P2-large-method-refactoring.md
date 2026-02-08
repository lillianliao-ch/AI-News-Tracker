---
title: "Large Methods Violating Single Responsibility Principle"
issue_id: "004"
priority: "P2"
status: "pending"
category: "code-quality"
severity: "medium"
created_at: "2026-01-16"
file: "lamda_scraper.py"
lines: "120-230"
estimated_effort: "4 hours"
tags: ["refactoring", "single-responsibility", "code-smell"]
---

# ⚠️ Large Methods Violating Single Responsibility Principle

## Problem Statement

Several methods in the codebase exceed 100 lines and handle multiple responsibilities, making the code:
- Difficult to understand and maintain
- Hard to test individual components
- Prone to bugs when making changes
- Violating Single Responsibility Principle (SRP)

## Current Implementation Issues

### Issue 1: `parse_personal_homepage()` Method (110+ lines)

**File**: `lamda_scraper.py:120-230`

```python
def parse_personal_homepage(self, url: str) -> dict:
    """解析个人主页，提取详细信息"""
    try:
        resp = self.session.get(url, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 1. Extract name (20 lines)
        # 2. Extract email (15 lines)
        # 3. Extract phone (10 lines)
        # 4. Extract bio (25 lines)
        # 5. Extract education (20 lines)
        # 6. Extract publications (30 lines)
        # ... all in one method

    except Exception as e:
        logger.error(f"Error parsing {url}: {e}")
        return {}
```

**Problems**:
- Does 6 different things in one method
- 110+ lines of code
- Cannot test extraction logic independently
- Cannot reuse extraction logic for other sites
- Hard to debug when one extraction fails

### Issue 2: Scoring Logic in `talent_analyzer.py`

**File**: `talent_analyzer.py:100-200`

```python
def calculate_talent_score(self, candidate: Candidate) -> float:
    """Calculate talent score"""
    # 1. GitHub analysis (40 lines)
    # 2. Publication analysis (30 lines)
    # 3. Education analysis (20 lines)
    # 4. Milestone calculation (20 lines)
    # 5. Weight application (15 lines)
    # All mixed together
```

## Impact Analysis

| Impact Area | Severity | Description |
|------------|----------|-------------|
| **Maintainability** | High | Changes require understanding entire method |
| **Testability** | High | Cannot test individual extraction logic |
| **Reusability** | High | Cannot reuse extraction for other sites |
| **Debugging** | High | Hard to isolate which extraction failed |
| **Code Review** | Medium | Large methods are hard to review |

## Proposed Solutions

### Solution 1: Extract Individual Parsers (Recommended)

**Before** (110+ lines):

```python
def parse_personal_homepage(self, url: str) -> dict:
    """Extract all info from personal homepage"""
    # All extraction logic mixed together
    # ... 110+ lines
```

**After** (broken into smaller methods):

```python
class PersonalHomepageParser:
    """Parse personal homepage with dedicated extractors"""

    def parse(self, url: str) -> dict:
        """Parse personal homepage - orchestrate extraction"""
        try:
            soup = self._fetch_page(url)

            return {
                'name': self._extract_name(soup),
                'email': self._extract_email(soup),
                'phone': self._extract_phone(soup),
                'bio': self._extract_bio(soup),
                'education': self._extract_education(soup),
                'publications': self._extract_publications(soup)
            }
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
            return {}

    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse page"""
        resp = self.session.get(url, timeout=30)
        return BeautifulSoup(resp.text, 'html.parser')

    def _extract_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract name from page"""
        # Name extraction logic (20 lines)
        selectors = [
            'h1.name',
            '.person-name',
            '[itemprop="name"]'
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        return None

    def _extract_email(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract email from page"""
        # Email extraction logic (15 lines)
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # Try meta tags
        meta_email = soup.find('meta', attrs={'name': 'email'})
        if meta_email:
            return meta_email.get('content')

        # Try mailto links
        mailto = soup.find('a', href=re.compile(r'^mailto:'))
        if mailto:
            return mailto['href'].replace('mailto:', '')

        # Search text for email pattern
        text = soup.get_text()
        match = email_pattern.search(text)
        if match:
            return match.group()

        return None

    def _extract_phone(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract phone number"""
        # Phone extraction logic (10 lines)
        phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

        text = soup.get_text()
        match = phone_pattern.search(text)
        if match:
            return match.group()

        return None

    def _extract_bio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract biography"""
        # Bio extraction logic (25 lines)
        bio_selectors = [
            '.bio',
            '.biography',
            '[itemprop="description"]',
            '#profile-bio'
        ]

        for selector in bio_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True, separator=' ')

        return None

    def _extract_education(self, soup: BeautifulSoup) -> List[dict]:
        """Extract education history"""
        # Education extraction logic (20 lines)
        education = []
        edu_items = soup.select('.education-item, .edu-item')

        for item in edu_items:
            edu = {
                'school': item.select_one('.school').get_text(strip=True) if item.select_one('.school') else None,
                'degree': item.select_one('.degree').get_text(strip=True) if item.select_one('.degree') else None,
                'year': item.select_one('.year').get_text(strip=True) if item.select_one('.year') else None,
            }
            education.append(edu)

        return education

    def _extract_publications(self, soup: BeautifulSoup) -> List[dict]:
        """Extract publications"""
        # Publication extraction logic (30 lines)
        publications = []
        pub_items = soup.select('.publication, .pub-item')

        for item in pub_items:
            pub = {
                'title': item.select_one('.title').get_text(strip=True) if item.select_one('.title') else None,
                'venue': item.select_one('.venue').get_text(strip=True) if item.select_one('.venue') else None,
                'year': item.select_one('.year').get_text(strip=True) if item.select_one('.year') else None,
            }
            publications.append(pub)

        return publications
```

### Solution 2: Strategy Pattern for Different Site Types

```python
from abc import ABC, abstractmethod

class SiteParser(ABC):
    """Base parser for different site types"""

    @abstractmethod
    def parse(self, url: str) -> dict:
        """Parse site and extract info"""
        pass

class AcademicSiteParser(SiteParser):
    """Parser for academic websites"""

    def __init__(self):
        self.extractors = {
            'name': NameExtractor(),
            'email': EmailExtractor(),
            'phone': PhoneExtractor(),
            'bio': BioExtractor()
        }

    def parse(self, url: str) -> dict:
        soup = self._fetch_page(url)
        return {
            key: extractor.extract(soup)
            for key, extractor in self.extractors.items()
        }

class GitHubSiteParser(SiteParser):
    """Parser for GitHub profiles"""

    def parse(self, url: str) -> dict:
        # GitHub-specific parsing
        pass

class PersonalHomepageFactory:
    """Factory for creating appropriate parser"""

    @staticmethod
    def create_parser(url: str) -> SiteParser:
        if 'github.com' in url:
            return GitHubSiteParser()
        else:
            return AcademicSiteParser()
```

### Solution 3: Refactor Talent Analyzer

**Before** (single 100-line method):

```python
def calculate_talent_score(self, candidate: Candidate) -> float:
    # All logic mixed together
```

**After** (modular components):

```python
class TalentAnalyzer:
    """Analyze candidate talent with modular components"""

    def __init__(self):
        self.github_analyzer = GitHubAnalyzer()
        self.pub_analyzer = PublicationAnalyzer()
        self.edu_analyzer = EducationAnalyzer()
        self.milestone_analyzer = MilestoneAnalyzer()

    def calculate_talent_score(self, candidate: Candidate) -> float:
        """Calculate overall talent score"""
        scores = {
            'github': self.github_analyzer.analyze(candidate.github),
            'publications': self.pub_analyzer.analyze(candidate.publications),
            'education': self.edu_analyzer.analyze(candidate.education),
            'milestones': self.milestone_analyzer.analyze(candidate.milestones)
        }

        return self._apply_weights(scores)

class GitHubAnalyzer:
    """Analyze GitHub profile"""

    def analyze(self, github_username: str) -> float:
        if not github_username:
            return 0.0

        # GitHub analysis logic (40 lines)
        repos_score = self._analyze_repos(github_username)
        activity_score = self._analyze_activity(github_username)

        return (repos_score + activity_score) / 2

    def _analyze_repos(self, username: str) -> float:
        """Analyze repositories"""
        # Repo-specific logic
        pass

    def _analyze_activity(self, username: str) -> float:
        """Analyze recent activity"""
        # Activity-specific logic
        pass
```

## Recommended Action Plan

1. **Phase 1** (Week 1):
   - [ ] Extract individual parser methods from `parse_personal_homepage()`
   - [ ] Create `PersonalHomepageParser` class
   - [ ] Add unit tests for each extractor
   - [ ] Verify functionality preserved

2. **Phase 2** (Week 2):
   - [ ] Refactor `talent_analyzer.py` with modular components
   - [ ] Create analyzer classes (GitHub, Publication, Education)
   - [ ] Add unit tests for each analyzer
   - [ ] Verify scoring consistency

3. **Phase 3** (Week 3):
   - [ ] Implement strategy pattern for different site types
   - [ ] Create factory for parser selection
   - [ ] Add integration tests
   - [ ] Update documentation

## Testing Strategy

### Before Refactoring

1. Add characterization tests to capture current behavior
2. Run tests to ensure they pass
3. Use these as regression tests during refactoring

```python
def test_parse_personal_homepage_current_behavior():
    """Test current behavior before refactoring"""
    parser = PersonalHomepageParser()
    result = parser.parse("http://example.com/person")

    # Characterize current behavior
    assert result['name'] == 'John Doe'
    assert result['email'] == 'john@example.com'
```

### After Refactoring

```python
def test_name_extractor():
    """Test name extraction in isolation"""
    extractor = NameExtractor()
    soup = BeautifulSoup('<h1 class="name">John Doe</h1>', 'html.parser')

    name = extractor.extract(soup)

    assert name == 'John Doe'

def test_email_extractor():
    """Test email extraction in isolation"""
    extractor = EmailExtractor()
    soup = BeautifulSoup('<a href="mailto:test@example.com">Email</a>', 'html.parser')

    email = extractor.extract(soup)

    assert email == 'test@example.com'
```

## Refactoring Checklist

- [ ] Add characterization tests for current behavior
- [ ] Extract first method (e.g., `_extract_name()`)
- [ ] Run tests to verify no functionality lost
- [ ] Extract second method (e.g., `_extract_email()`)
- [ ] Run tests again
- [ ] Continue until all methods extracted
- [ ] Add unit tests for each extracted method
- [ ] Update docstrings
- [ ] Update documentation

## Benefits of Refactoring

| Benefit | Impact |
|---------|--------|
| **Testability** | Can test each extractor independently |
| **Reusability** | Extractors can be reused for other sites |
| **Maintainability** | Easier to understand and modify |
| **Debugging** | Can isolate which extraction failed |
| **Extensibility** | Easy to add new extractors |

## Related Issues

- Issue #003: Configuration Hardcoding
- Issue #008: Missing Unit Tests
- Issue #009: No Integration Tests

## References

- [Refactoring: Extract Method](https://refactoring.guru/extract-method)
- [Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)

---

**Assigned To**: TBD
**Due Date**: 2026-02-06 (Medium Priority)
**Dependencies**: Issue #008 (Add tests first)
