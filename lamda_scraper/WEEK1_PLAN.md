# 🔒 Week 1: Fix Critical Security Issues - Implementation Plan

**Week**: 2026-01-16 to 2026-01-23
**Goal**: Fix all P1 critical security vulnerabilities
**Estimated Total Time**: 3-4 hours

---

## 📋 Week 1 Task Breakdown

### Task 1: Fix SSL Verification (Issue #001) ⏱️ 30 minutes
**Priority**: 🔴 CRITICAL
**File**: `scrape_websites_for_contacts.py:16-17`

**Current (INSECURE)**:
```python
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
resp = self.session.get(website_url, timeout=30, verify=False)
```

**Target (SECURE)**:
```python
# Remove warning suppression
resp = self.session.get(website_url, timeout=30, verify=True)
```

**Steps**:
1. ✅ Read `scrape_websites_for_contacts.py`
2. ✅ Remove `urllib3.disable_warnings()` line
3. ✅ Change `verify=False` to `verify=True`
4. ✅ Add SSL error handling with logging
5. ✅ Test with real websites

---

### Task 2: Implement GitHub Token Management (Issue #002) ⏱️ 1 hour
**Priority**: 🔴 CRITICAL
**File**: New file `github_token_manager.py` + update `github_enricher.py`

**What to Implement**:
1. Create `GitHubTokenConfig` class with:
   - Token validation on startup
   - Rate limit tracking
   - Safe token logging (hash-based)
   - Token rotation support

2. Update `GitHubEnricher` to use new token manager

**Steps**:
1. ✅ Create `github_token_manager.py`
2. ✅ Implement `GitHubTokenConfig` dataclass
3. ✅ Add token validation method
4. ✅ Add rate limit tracking
5. ✅ Add safe token identifier method
6. ✅ Update `GitHubEnricher.__init__()` to use token config
7. ✅ Add validation call in constructor
8. ✅ Test with real GitHub token

---

### Task 3: Create requirements.txt (Issue #009) ⏱️ 30 minutes
**Priority**: 🔴 HIGH
**File**: New file `requirements.txt`

**Dependencies to Include**:
```
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
pandas==2.1.1
openpyxl==3.1.2
python-dotenv==1.0.0
loguru==0.7.2
```

**Also create** `requirements-dev.txt`:
```
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
requests-mock==1.11.0
black==23.9.1
flake8==6.1.0
```

---

### Task 4: Create .env.example (Issue #009) ⏱️ 15 minutes
**Priority**: 🔴 HIGH
**File**: New file `.env.example`

**Content**:
```bash
# GitHub API Token (optional)
# Get yours at: https://github.com/settings/tokens
GITHUB_TOKEN=

# HTTP Settings
HTTP_TIMEOUT=30
HTTP_DELAY=1.0

# Output Settings
OUTPUT_DIR=./data
LOG_LEVEL=INFO
```

---

### Task 5: Basic Input Validation (Issue #010) ⏱️ 1 hour
**Priority**: 🔴 HIGH
**File**: New file `models.py` + update `lamda_scraper.py`

**What to Implement**:
1. Create Pydantic models for:
   - `CandidateModel` with validators
   - URL validation
   - Email validation
   - GitHub username validation

2. Update scraper to validate before processing

**Steps**:
1. ✅ Create `models.py` with Pydantic models
2. ✅ Add validators for all fields
3. ✅ Add sanitization for bio field
4. ✅ Update `lamda_scraper.py` to use models
5. ✅ Add validation in entry points
6. ✅ Test with invalid data

---

## 📅 Daily Schedule

### Day 1 (2026-01-16): SSL Fix + Requirements
**Time**: 1 hour
**Tasks**:
- [ ] Fix SSL verification (30 min)
- [ ] Create requirements.txt (15 min)
- [ ] Create .env.example (15 min)

**Deliverables**:
- ✅ Secure SSL enabled
- ✅ `requirements.txt` created
- ✅ `.env.example` created

---

### Day 2 (2026-01-17): GitHub Token Management Part 1
**Time**: 1 hour
**Tasks**:
- [ ] Create `github_token_manager.py`
- [ ] Implement `GitHubTokenConfig` class
- [ ] Add token validation method
- [ ] Add rate limit tracking

**Deliverables**:
- ✅ Token manager class created
- ✅ Validation implemented

---

### Day 3 (2026-01-18): GitHub Token Management Part 2
**Time**: 1 hour
**Tasks**:
- [ ] Update `GitHubEnricher` to use token manager
- [ ] Add safe token logging
- [ ] Test with real GitHub API

**Deliverables**:
- ✅ Token manager integrated
- ✅ Tested and working

---

### Day 4 (2026-01-19): Input Validation
**Time**: 1 hour
**Tasks**:
- [ ] Create `models.py` with Pydantic
- [ ] Add validators for all fields
- [ ] Update scraper to validate data
- [ ] Test with edge cases

**Deliverables**:
- ✅ Data validation implemented
- ✅ All tests passing

---

### Day 5 (2026-01-20): Integration & Testing
**Time**: 1 hour
**Tasks**:
- [ ] Full integration test
- [ ] Test all security fixes
- [ ] Document changes
- [ ] Update README if needed

**Deliverables**:
- ✅ All security issues fixed
- ✅ Tests passing
- ✅ Documentation updated

---

## 🎯 Acceptance Criteria

### Task 1: SSL Verification
- [ ] All `verify=False` changed to `verify=True`
- [ ] No `urllib3.disable_warnings()` calls
- [ ] SSL errors logged appropriately
- [ ] Tested with 5+ real websites

### Task 2: Token Management
- [ ] Token validated on startup
- [ ] Rate limits tracked
- [ ] Token never logged in plain text
- [ ] Graceful handling of rate limit errors
- [ ] Tested with real GitHub API

### Task 3: Requirements
- [ ] `requirements.txt` created with all dependencies
- [ ] `requirements-dev.txt` created
- [ ] Versions pinned (==)
- [ ] `pip install -r requirements.txt` works

### Task 4: .env.example
- [ ] `.env.example` created
- [ ] All environment variables documented
- [ ] Comments explain where to get values
- [ ] `.env` added to `.gitignore`

### Task 5: Input Validation
- [ ] Pydantic models created
- [ ] All fields validated
- [ ] XSS prevented (HTML escaped)
- [ ] Invalid URLs rejected
- [ ] Invalid emails rejected
- [ ] Tested with edge cases

---

## 🧪 Testing Plan

### Test 1: SSL Verification
```bash
# Run scraper and verify no SSL warnings
python lamda_scraper.py --limit 5

# Check logs for successful HTTPS connections
```

### Test 2: GitHub Token Management
```bash
# Test with invalid token
GITHUB_TOKEN=invalid python github_enricher.py

# Should see: "Invalid GitHub token: 401"

# Test with valid token
GITHUB_TOKEN=ghp_xxx python github_enricher.py

# Should see: "Token validated: 4999 requests remaining"
```

### Test 3: Requirements Installation
```bash
# Fresh install test
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
# Should install without errors
```

### Test 4: Input Validation
```python
# Test invalid email
from models import CandidateModel
try:
    CandidateModel(
        name_cn="Test",
        email="not-an-email",  # Invalid
        source_type="alumni",
        data_source="test"
    )
except ValidationError as e:
    print(f"✅ Caught: {e}")

# Test XSS prevention
candidate = CandidateModel(
    name_cn="Test",
    bio="<script>alert('xss')</script>",
    source_type="alumni",
    data_source="test"
)
assert "<script>" not in candidate.bio
print("✅ XSS prevented")
```

---

## 📊 Progress Tracking

| Day | Task | Status | Time Spent |
|-----|------|--------|------------|
| Day 1 | SSL + Requirements | ⏳ Not started | 0h |
| Day 2 | Token Management Part 1 | ⏳ Not started | 0h |
| Day 3 | Token Management Part 2 | ⏳ Not started | 0h |
| Day 4 | Input Validation | ⏳ Not started | 0h |
| Day 5 | Integration & Testing | ⏳ Not started | 0h |

**Total Estimated Time**: 3-4 hours
**Total Actual Time**: TBD

---

## 🚨 Risk Management

### Risk 1: Breaking Existing Functionality
**Mitigation**:
- Test after each change
- Keep backup of original files
- Use git for version control

### Risk 2: GitHub API Rate Limiting
**Mitigation**:
- Implement rate limit tracking first
- Use test token with low quota
- Add logging for rate limit status

### Risk 3: SSL Certificate Errors
**Mitigation**:
- Add graceful error handling
- Log problematic URLs
- Allow per-URL SSL configuration (future)

---

## 📚 Resources

### SSL/TLS
- [Python requests: SSL Verification](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)
- [OWASP: Transport Layer Protection](https://owasp.org/www-project-top-ten/)

### GitHub API
- [GitHub API Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [Creating Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

### Pydantic Validation
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Field Validators](https://pydantic-docs.helpmanual.io/usage/validators/)

---

## ✅ Week 1 Success Criteria

By the end of Week 1, the following will be true:

- ✅ No SSL verification disabled
- ✅ GitHub tokens properly managed
- ✅ All dependencies documented
- ✅ Environment configured properly
- ✅ All user input validated
- ✅ No critical security vulnerabilities remain
- ✅ All changes tested and documented

---

## 🎉 Ready to Start!

**First Action**: Fix SSL verification in `scrape_websites_for_contacts.py`

**Command to start**:
```bash
cd /Users/lillianliao/notion_rag/lamda_scraper
# Open scrape_websites_for_contacts.py and change verify=False to verify=True
```

**Estimated completion**: End of Day 1 (1 hour)

---

**Plan Version**: v1.0
**Created**: 2026-01-16
**Status**: 📋 Ready to execute
**Next Review**: 2026-01-23 (End of Week 1)
