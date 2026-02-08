---
title: "Missing requirements.txt and Documentation"
issue_id: "009"
priority: "P3"
status": "pending"
category: "documentation"
severity: "low"
created_at: "2026-01-16"
file: "Project root"
estimated_effort: "2 hours"
tags: ["dependencies", "documentation", "setup"]
---

# ⚠️ Missing requirements.txt and Documentation

## Problem Statement

The project lacks:
1. `requirements.txt` for dependency management
2. `README.md` with setup instructions
3. Installation/usage documentation
4. Development setup guide

This makes it difficult for others to:
- Set up the project
- Understand dependencies
- Contribute to the project

## Current State

```bash
lamda_scraper/
├── lamda_scraper.py
├── github_enricher.py
├── talent_analyzer.py
└── # No requirements.txt, README.md, or docs
```

**Dependencies** (from code analysis):
- `requests`
- `beautifulsoup4`
- `pandas`
- `python-dotenv`

## Proposed Solutions

### Solution 1: Create requirements.txt

**Create `requirements.txt`**:

```txt
# Web Scraping
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3

# Data Processing
pandas==2.1.1
openpyxl==3.1.2

# Configuration
python-dotenv==1.0.0

# Logging
loguru==0.7.2

# GitHub API (if using specific client)
# PyGitHub==2.1.1
```

**Create `requirements-dev.txt`**:

```txt
# Testing
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
requests-mock==1.11.0

# Code Quality
black==23.9.1
flake8==6.1.0
mypy==1.5.1
isort==5.12.0

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==1.3.0
```

### Solution 2: Create Comprehensive README

**Create `README.md`**:

```markdown
# LAMDA Alumni Scraper

Scrapes LAMDA Lab alumni and PhD students information from official website and enriches with GitHub data.

## Features

- Scrape alumni and PhD students from LAMDA Lab website
- Extract personal information (name, email, website, etc.)
- Enrich with GitHub profile data
- Calculate talent scores based on publications and GitHub activity
- Export to CSV and JSON formats

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd lamda_scraper
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your GitHub token
```

## Usage

### Basic Usage

Scrape with default settings:
```bash
python lamda_scraper.py
```

### Advanced Options

Limit number of candidates:
```bash
python lamda_scraper.py --limit 10
```

Specify output format:
```bash
python lamda_scraper.py --output-format json
```

Enable GitHub enrichment:
```bash
python lamda_scraper.py --enable-github
```

### Configuration

Create a `.env` file in the project root:

```bash
# GitHub API Token (optional, for enrichment)
GITHUB_TOKEN=ghp_your_token_here

# HTTP Settings
HTTP_TIMEOUT=30
HTTP_DELAY=1.0

# Output Settings
OUTPUT_DIR=./data
LOG_LEVEL=INFO
```

## Output

The scraper generates:

1. `candidates.csv` - Tabular data
2. `candidates.json` - Structured data
3. `talent_scores.json` - Scoring results

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=lamda_scraper --cov-report=html
```

### Code Formatting

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8 .
```

## Project Structure

```
lamda_scraper/
├── lamda_scraper.py          # Main scraper
├── github_enricher.py        # GitHub API integration
├── talent_analyzer.py        # Talent scoring
├── config/
│   └── config.yaml           # Configuration file
├── data/                     # Output directory
├── tests/                    # Test suite
├── requirements.txt          # Dependencies
├── requirements-dev.txt      # Dev dependencies
└── README.md                 # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests: `pytest`
6. Submit a pull request

## License

MIT License

## Contact

For questions or issues, please open a GitHub issue.
```

### Solution 3: Create .env.example

**Create `.env.example`**:

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

# Scraping Settings
MAX_RETRIES=3
ENABLE_CACHE=true
```

### Solution 4: Create Setup Script

**Create `setup.sh`**:

```bash
#!/bin/bash

echo "🚀 Setting up LAMDA Alumni Scraper"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GitHub token"
else
    echo "✅ .env file already exists"
fi

# Create output directory
mkdir -p data

echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GitHub token (optional)"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run scraper: python lamda_scraper.py"
```

**Make executable**:
```bash
chmod +x setup.sh
```

### Solution 5: Create Development Guide

**Create `docs/DEVELOPMENT.md`**:

```markdown
# Development Guide

## Setting Up Development Environment

1. Clone and setup:
```bash
git clone <repository-url>
cd lamda_scraper
./setup.sh
```

2. Install dev dependencies:
```bash
source venv/bin/activate
pip install -r requirements-dev.txt
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lamda_scraper --cov-report=html

# Run specific test
pytest tests/test_scraper.py::TestLAMDAScraper::test_extract_email
```

## Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

Format code before committing:
```bash
black .
isort .
flake8 .
```

## Project Structure

```
lamda_scraper/
├── lamda_scraper.py          # Main scraper logic
├── github_enricher.py        # GitHub API client
├── talent_analyzer.py        # Scoring algorithm
├── config/                   # Configuration files
├── tests/                    # Test suite
│   ├── conftest.py
│   ├── test_scraper.py
│   └── test_github_enricher.py
└── docs/                     # Documentation
```

## Adding New Features

1. Create a feature branch
2. Write tests first (TDD)
3. Implement feature
4. Run tests
5. Update documentation
6. Submit PR

## Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python lamda_scraper.py
```

## Common Issues

### Issue: GitHub API Rate Limit
**Solution**: Add token to `.env` file

### Issue: SSL Certificate Errors
**Solution**: See Issue #001 in todos/

### Issue: Import Errors
**Solution**: Ensure virtual environment is activated
```

## Recommended Action Plan

1. **Immediate** (Day 1):
   - [ ] Create `requirements.txt`
   - [ ] Create `requirements-dev.txt`
   - [ ] Create `.env.example`

2. **Short-term** (Week 1):
   - [ ] Create comprehensive `README.md`
   - [ ] Create `setup.sh` script
   - [ ] Create development guide

3. **Long-term** (Week 2):
   - [ ] Add API documentation
   - [ ] Add architecture diagrams
   - [ ] Add troubleshooting guide

## Benefits

| Benefit | Impact |
|---------|--------|
| **Easy setup** | New users can start in 5 minutes |
| **Clear dependencies** | Know exactly what's needed |
| **Better collaboration** | Others can contribute |
| **Professional** | Shows project maturity |

## Related Issues

- Issue #003: Configuration Hardcoding
- Issue #008: Missing Unit Tests

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [README Best Practices](https://www.makeareadme.com/)
- [Configuration Management](https://12factor.net/config)

---

**Assigned To**: TBD
**Due Date**: 2026-01-23 (Low Priority - Quick Win)
**Dependencies**: None
