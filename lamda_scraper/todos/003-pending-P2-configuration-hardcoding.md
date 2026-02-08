---
title: "Hard-coded Configuration Values - Maintainability Issue"
issue_id: "003"
priority: "P2"
status: "pending"
category: "code-quality"
severity: "medium"
created_at: "2026-01-16"
file: "lamda_scraper.py"
lines: "25-35, 50-60"
estimated_effort: "2 hours"
tags: ["configuration", "maintainability", "hardcoding"]
---

# ⚠️ Hard-coded Configuration Values - Maintainability Issue

## Problem Statement

Configuration values (URLs, headers, weights, delays) are hard-coded throughout the codebase. This makes the application:
- Difficult to maintain and modify
- Hard to test with different configurations
- Impossible to deploy across environments
- Risk of breaking when external values change

## Current Implementation Issues

### Issue 1: Hard-coded URLs and Headers

**File**: `lamda_scraper.py:25-35`

```python
URLS = {
    "alumni": "https://www.lamda.nju.edu.cn/People/Alumni.html",
    "phd": "https://www.lamda.nju.edu.cn/People/PhD.html"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

**Problems**:
- Cannot change without editing code
- No environment-specific configurations (dev/test/prod)
- Cannot be overridden at runtime

### Issue 2: Hard-coded Scoring Weights

**File**: `talent_analyzer.py:80-100`

```python
VENUE_WEIGHTS = {
    "NeurIPS": 1.0,
    "ICML": 1.0,
    "CVPR": 0.95,
    # ... 50+ lines of weights
}

MILESTONE_WEIGHTS = {
    "phd": 5.0,
    "postdoc": 3.0,
    "faculty": 10.0
}
```

**Problems**:
- Cannot tune without code changes
- Hard to A/B test different weight configurations
- Requires redeployment to adjust

### Issue 3: Hard-coded Timeouts and Delays

**File**: `lamda_scraper.py:45-50`

```python
class LAMDAScraper:
    def __init__(self, delay: float = 1.0):  # Hard-coded default
        self.delay = delay
        self.timeout = 30  # Hard-coded
```

**Problems**:
- Cannot adjust for different network conditions
- No per-request timeout configuration
- Fixed delay prevents adaptive throttling

## Impact Analysis

| Impact Area | Severity | Description |
|------------|----------|-------------|
| **Maintainability** | High | Changes require code editing and redeployment |
| **Testing** | High | Cannot test with mock configurations easily |
| **Deployment** | Medium | Same config across all environments |
| **Flexibility** | High | Cannot adjust without developer intervention |
| **Collaboration** | Medium | Non-technical users cannot adjust parameters |

## Proposed Solutions

### Solution 1: Configuration File with YAML (Recommended)

Create `config.yaml`:

```yaml
# application/config.yaml

# URLs
urls:
  alumni: "https://www.lamda.nju.edu.cn/People/Alumni.html"
  phd: "https://www.lamda.nju.edu.cn/People/PhD.html"

# HTTP settings
http:
  timeout: 30
  delay: 1.0
  max_retries: 3
  headers:
    User-Agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Scoring weights
scoring:
  venue_weights:
    NeurIPS: 1.0
    ICML: 1.0
    CVPR: 0.95
    ICCV: 0.9
    # ... more weights

  milestone_weights:
    phd: 5.0
    postdoc: 3.0
    faculty: 10.0

# Data paths
paths:
  output_dir: "./data"
  cache_dir: "./cache"
  log_dir: "./logs"

# GitHub settings
github:
  max_repos: 50
  api_timeout: 30
  enable_cache: true

# Environments (can override)
environments:
  development:
    http:
      delay: 0.5  # Faster for local testing
  production:
    http:
      delay: 2.0  # More conservative
```

Create `config.py`:

```python
from dataclasses import dataclass
from typing import Dict, Any
import yaml
from pathlib import Path

@dataclass
class HTTPConfig:
    timeout: int = 30
    delay: float = 1.0
    max_retries: int = 3
    headers: Dict[str, str] = None

@dataclass
class ScoringConfig:
    venue_weights: Dict[str, float] = None
    milestone_weights: Dict[str, float] = None

@dataclass
class GitHubConfig:
    max_repos: int = 50
    api_timeout: int = 30
    enable_cache: bool = True

@dataclass
class Config:
    urls: Dict[str, str] = None
    http: HTTPConfig = None
    scoring: ScoringConfig = None
    github: GitHubConfig = None
    paths: Dict[str, str] = None

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "Config":
        """Load configuration from YAML file"""
        config_path = Path(path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Parse environment-specific overrides
        env = os.getenv("APP_ENV", "development")
        if "environments" in data and env in data["environments"]:
            env_overrides = data["environments"][env]
            data = cls._merge_configs(data, env_overrides)

        return cls(
            urls=data.get("urls", {}),
            http=HTTPConfig(**data.get("http", {})),
            scoring=ScoringConfig(**data.get("scoring", {})),
            github=GitHubConfig(**data.get("github", {})),
            paths=data.get("paths", {})
        )

    @staticmethod
    def _merge_configs(base: Dict, override: Dict) -> Dict:
        """Deep merge configuration dicts"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

# Usage
config = Config.from_yaml()
scraper = LAMDAScraper(
    delay=config.http.delay,
    timeout=config.http.timeout
)
```

### Solution 2: Environment Variables with Pydantic

```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # URLs
    ALUMNI_URL: str = "https://www.lamda.nju.edu.cn/People/Alumni.html"
    PHD_URL: str = "https://www.lamda.nju.edu.cn/People/PhD.html"

    # HTTP
    HTTP_TIMEOUT: int = 30
    HTTP_DELAY: float = 1.0
    MAX_RETRIES: int = 3

    # Paths
    OUTPUT_DIR: str = "./data"
    CACHE_DIR: str = "./cache"

    # GitHub
    GITHUB_MAX_REPOS: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

Create `.env`:

```bash
# .env
ALUMNI_URL=https://www.lamda.nju.edu.cn/People/Alumni.html
HTTP_TIMEOUT=30
HTTP_DELAY=1.0
OUTPUT_DIR=./data
```

### Solution 3: Command-Line Arguments with Click

```python
import click

@click.command()
@click.option('--config', '-c', default='config.yaml', help='Config file path')
@click.option('--delay', type=float, help='Delay between requests')
@click.option('--output-dir', type=click.Path(), help='Output directory')
@click.option('--env', type=click.Choice(['dev', 'prod']), default='dev')
def main(config, delay, output_dir, env):
    """LAMDA Alumni Scraper"""
    cfg = Config.from_yaml(config)

    # Override with CLI args
    if delay:
        cfg.http.delay = delay
    if output_dir:
        cfg.paths['output_dir'] = output_dir

    scraper = LAMDAScraper(delay=cfg.http.delay)
    scraper.run()

if __name__ == '__main__':
    main()
```

Usage:
```bash
# Use default config
python lamda_scraper.py

# Override specific values
python lamda_scraper.py --delay 2.0 --output-dir ./output

# Use different environment
python lamda_scraper.py --env prod
```

### Solution 4: Hybrid Approach (Best Practice)

Combine all three approaches:

```python
# 1. Default values in config.yaml
# 2. Environment variables for secrets
# 3. CLI args for runtime overrides

@click.command()
@click.option('--config', '-c', default='config.yaml')
@click.option('--delay', type=float)
@click.option('--env', default='development')
def main(config, delay, env):
    # Load from file
    cfg = Config.from_yaml(config)

    # Override with environment
    os.environ["APP_ENV"] = env

    # Override with CLI args
    if delay:
        cfg.http.delay = delay

    return cfg
```

## Recommended Action Plan

1. **Phase 1** (Week 1):
   - [ ] Create `config.yaml` with all current configurations
   - [ ] Create `Config` dataclass with loader
   - [ ] Add Pydantic for validation
   - [ ] Document all configuration options

2. **Phase 2** (Week 2):
   - [ ] Refactor `lamda_scraper.py` to use config
   - [ ] Refactor `talent_analyzer.py` to use config
   - [ ] Refactor `github_enricher.py` to use config
   - [ ] Add config validation on startup

3. **Phase 3** (Week 3):
   - [ ] Add CLI argument overrides
   - [ ] Add environment-specific configs
   - [ ] Create example config files
   - [ ] Update documentation

## File Structure

```
lamda_scraper/
├── config/
│   ├── __init__.py
│   ├── config.py           # Config class
│   ├── config.yaml         # Default config
│   ├── config.dev.yaml     # Dev overrides
│   ├── config.prod.yaml    # Prod overrides
│   └── schema.py           # Pydantic models
├── .env                    # Environment variables
├── .env.example            # Example env vars
└── lamda_scraper.py        # Use config
```

## Testing Checklist

- [ ] Test loading default config
- [ ] Test environment-specific overrides
- [ ] Test CLI argument overrides
- [ ] Test invalid config detection
- [ ] Test missing config file handling
- [ ] Test config validation (types, ranges)
- [ ] Add unit tests for config loading

## Migration Strategy

1. Keep hard-coded values as defaults in config
2. Gradually migrate each module to use config
3. Maintain backward compatibility during transition
4. Add deprecation warnings for old code

## Related Issues

- Issue #002: GitHub Token Management
- Issue #005: Large Methods Need Refactoring
- Issue #008: Missing Unit Tests

## References

- [12-Factor App: Config](https://12factor.net/config)
- [Python YAML Best Practices](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Click Documentation](https://click.palletsprojects.com/)
- [Pydantic Settings](https://pydantic-docs.helpmanual.io/usage/settings/)

---

**Assigned To**: TBD
**Due Date**: 2026-02-06 (Medium Priority)
**Dependencies**: None
