---
title: "Serial Processing - Performance Bottleneck"
issue_id: "007"
priority: "P3"
status: "pending"
category: "performance"
severity: "medium"
created_at: "2026-01-16"
file: "lamda_scraper.py, github_enricher.py"
lines: "multiple"
estimated_effort: "6 hours"
tags: ["performance", "concurrency", "async-io"]
---

# ⚠️ Serial Processing - Performance Bottleneck

## Problem Statement

The scraper processes candidates, API calls, and website scraping sequentially, creating a significant performance bottleneck. With 274 candidates and multiple operations per candidate, execution time is unnecessarily long.

## Current Implementation Issues

### Issue 1: Sequential Candidate Processing

**File**: `lamda_scraper.py:250-270`

```python
def run(self):
    """Run scraper"""
    candidates = []

    # Process alumni sequentially
    for url in URLS['alumni']:
        candidate_data = self.parse_personal_homepage(url)
        candidates.append(candidate_data)

    # Process PhD students sequentially
    for url in URLS['phd']:
        candidate_data = self.parse_personal_homepage(url)
        candidates.append(candidate_data)

    return candidates
```

**Impact**:
- If each page takes 1 second to parse: 274 candidates × 1s = **4.5 minutes**
- With GitHub enrichment: +30 seconds per candidate = **2.3 hours**
- With website scraping: +10 seconds per candidate = **7.6 hours**

### Issue 2: Sequential API Calls

**File**: `github_enricher.py:100-120`

```python
def enrich_multiple(self, candidates: list) -> list:
    """Enrich multiple candidates with GitHub data"""
    enriched = []

    for candidate in candidates:
        if candidate.github:
            github_data = self.get_user_info(candidate.github)
            repos_data = self.get_user_repos(candidate.github)
            # Merge data
            enriched.append(merged_data)

    return enriched
```

**Impact**:
- 274 candidates × 3 API calls = 822 API calls
- At 500ms per call = **6.8 minutes** (network latency bound)

### Issue 3: Sequential Website Scraping

**File**: `scrape_websites_for_contacts.py:50-70`

```python
def scrape_all_websites(self, candidates: list) -> list:
    """Scrape all personal websites"""
    results = []

    for candidate in candidates:
        if candidate.website:
            contact_info = self.scrape_website(candidate.website)
            results.append(contact_info)

    return results
```

**Impact**:
- 274 websites × 10 seconds = **45.6 minutes**

## Performance Impact

| Operation | Current Time | Parallel (10 workers) | Speedup |
|-----------|--------------|----------------------|---------|
| **Parse 274 pages** | 4.5 min | 27 sec | **10x** |
| **822 GitHub API calls** | 6.8 min | 41 sec | **10x** |
| **Scrape 274 websites** | 45.6 min | 4.6 min | **10x** |
| **Total execution** | ~3 hours | ~18 min | **10x** |

## Proposed Solutions

### Solution 1: Concurrent Futures with ThreadPoolExecutor (Recommended)

**For I/O-bound operations** (HTTP requests, API calls):

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any
import logging

class ParallelScraper:
    """Scraper with parallel processing support"""

    def __init__(self, max_workers: int = 10):
        """
        Args:
            max_workers: Number of parallel workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def process_parallel(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        desc: str = "Processing"
    ) -> List[Any]:
        """
        Process items in parallel

        Args:
            items: List of items to process
            process_func: Function to apply to each item
            desc: Description for progress logging

        Returns:
            List of results
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_func, item): item
                for item in items
            }

            # Process as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]

                try:
                    result = future.result()
                    results.append(result)

                except Exception as e:
                    logging.error(f"Error processing {item}: {e}")
                    results.append(None)

        return results

# Usage
class LAMDAScraper:
    def run_parallel(self):
        """Run scraper with parallel processing"""
        parallel = ParallelScraper(max_workers=10)

        # Get all URLs
        alumni_urls = self.get_alumni_urls()
        phd_urls = self.get_phd_urls()
        all_urls = alumni_urls + phd_urls

        # Parse all pages in parallel
        candidates = parallel.process_parallel(
            items=all_urls,
            process_func=self.parse_personal_homepage,
            desc="Parsing pages"
        )

        # Filter out None values
        candidates = [c for c in candidates if c]

        return candidates
```

### Solution 2: Async IO with aiohttp (Higher Performance)

**For even better performance with async/await**:

```python
import aiohttp
import asyncio
from typing import List, Dict, Any

class AsyncLAMDAScraper:
    """Async scraper using aiohttp"""

    def __init__(self, max_concurrent: int = 20):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def parse_page_async(self, session: aiohttp.ClientSession, url: str) -> dict:
        """Parse single page asynchronously"""
        async with self.semaphore:  # Limit concurrency
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    html = await resp.text()

                soup = BeautifulSoup(html, 'html.parser')
                return self.extract_data(soup)

            except Exception as e:
                logging.error(f"Error parsing {url}: {e}")
                return None

    async def run_parallel(self, urls: List[str]) -> List[dict]:
        """Parse all pages in parallel"""
        # Create HTTP session with connection pooling
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                self.parse_page_async(session, url)
                for url in urls
            ]

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors and None values
        return [r for r in results if r and not isinstance(r, Exception)]

# Usage
async def main():
    scraper = AsyncLAMDAScraper(max_concurrent=20)

    alumni_urls = ["https://..."] * 274

    candidates = await scraper.run_parallel(alumni_urls)

    print(f"Parsed {len(candidates)} candidates")

if __name__ == "__main__":
    asyncio.run(main())
```

### Solution 3: Parallel GitHub Enrichment

```python
from concurrent.futures import ThreadPoolExecutor

class ParallelGitHubEnricher(GitHubEnricher):
    """GitHub enricher with parallel processing"""

    def enrich_parallel(self, candidates: List[dict], max_workers: int = 10) -> List[dict]:
        """Enrich multiple candidates in parallel"""
        results = {}

        def enrich_single(candidate):
            try:
                github_data = self.enrich_candidate(candidate)
                return (candidate['id'], github_data)
            except Exception as e:
                logging.error(f"Error enriching {candidate['name']}: {e}")
                return (candidate['id'], None)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all enrichment tasks
            futures = [
                executor.submit(enrich_single, candidate)
                for candidate in candidates
            ]

            # Collect results as they complete
            for future in as_completed(futures):
                candidate_id, github_data = future.result()

                if github_data:
                    results[candidate_id] = github_data

        # Merge results back into candidates
        for candidate in candidates:
            if candidate['id'] in results:
                candidate.update(results[candidate['id']])

        return candidates
```

### Solution 4: Batch API Calls

```python
class BatchGitHubEnricher(GitHubEnricher):
    """GitHub enricher with batch API calls"""

    async def get_users_batch(self, usernames: List[str]) -> List[dict]:
        """Get multiple users in batch using GraphQL"""
        # GitHub GraphQL can fetch multiple users in one request

        query = """
        query($usernames: [String!]!) {
            users(usernames: $usernames) {
                name
                bio
                followers
                repositories(first: 10) {
                    edges {
                        node {
                            name
                            stars
                        }
                    }
                }
            }
        }
        """

        # Batch size limit: 100 users per query
        BATCH_SIZE = 100

        results = []

        for i in range(0, len(usernames), BATCH_SIZE):
            batch = usernames[i:i+BATCH_SIZE]

            try:
                resp = await self._graphql_query(query, {'usernames': batch})
                results.extend(resp['data']['users'])

            except Exception as e:
                logging.error(f"Batch query failed: {e}")
                # Fallback to individual calls
                results.extend(await self._get_users_individually(batch))

        return results
```

### Solution 5: Progress Tracking

```python
from tqdm import tqdm

class ParallelScraperWithProgress:
    """Parallel scraper with progress tracking"""

    def process_with_progress(
        self,
        items: List[Any],
        process_func: Callable,
        desc: str = "Processing"
    ) -> List[Any]:
        """Process items in parallel with progress bar"""

        results = [None] * len(items)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(process_func, item): idx
                for idx, item in enumerate(items)
            }

            # Process with progress bar
            with tqdm(total=len(items), desc=desc) as pbar:
                for future in as_completed(futures):
                    idx = futures[future]

                    try:
                        results[idx] = future.result()

                    except Exception as e:
                        logging.error(f"Error at index {idx}: {e}")
                        results[idx] = None

                    finally:
                        pbar.update(1)

        return results
```

## Recommended Action Plan

1. **Phase 1** (Week 1):
   - [ ] Implement `ParallelScraper` with ThreadPoolExecutor
   - [ ] Add parallel page parsing
   - [ ] Add progress tracking with tqdm
   - [ ] Test with 10-20 pages

2. **Phase 2** (Week 2):
   - [ ] Implement parallel GitHub enrichment
   - [ ] Add rate limiting to respect API limits
   - [ ] Add error handling for parallel tasks
   - [ ] Test with full dataset

3. **Phase 3** (Week 3 - Optional):
   - [ ] Implement async version with aiohttp
   - [ ] Add connection pooling
   - [ ] Add semaphore for concurrency control
   - [ ] Benchmark vs ThreadPoolExecutor

## Performance Comparison

### Current (Serial)

```python
# 274 candidates × 3 operations
parse_time = 274 × 1s = 274s (4.5 min)
github_time = 274 × 30s = 8220s (2.3 hr)
website_time = 274 × 10s = 2740s (45.6 min)
total = ~3.4 hours
```

### With Parallel Processing (10 workers)

```python
parse_time = 274s / 10 = 27.4s
github_time = 8220s / 10 = 822s (13.7 min)
website_time = 2740s / 10 = 274s (4.6 min)
total = ~18.5 minutes

# Speedup: 11x faster
```

### With Async (20 concurrent)

```python
parse_time = 274s / 20 = 13.7s
github_time = 8220s / 20 = 411s (6.8 min)
website_time = 2740s / 20 = 137s (2.3 min)
total = ~9.5 minutes

# Speedup: 21x faster
```

## Rate Limiting

When adding parallel processing, respect rate limits:

```python
import time
from threading import Lock

class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate: float, capacity: int = 10):
        """
        Args:
            rate: Requests per second
            capacity: Maximum burst capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_time = time.time()
        self.lock = Lock()

    def acquire(self):
        """Acquire token (blocks if rate limit reached)"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_time

            # Refill tokens
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )

            if self.tokens < 1:
                # Wait for token
                sleep_time = (1 - self.tokens) / self.rate
                time.sleep(sleep_time)
                self.tokens = 0
            else:
                self.tokens -= 1

            self.last_time = now

# Usage
rate_limiter = RateLimiter(rate=5.0)  # 5 requests/second (GitHub limit)

def fetch_with_rate_limit(url):
    rate_limiter.acquire()
    return requests.get(url)
```

## Worker Count Recommendations

| Operation | Recommended Workers | Rationale |
|-----------|-------------------|-----------|
| **Page parsing** | 20-50 | I/O bound, can handle many |
| **GitHub API** | 5-10 | Rate limited (5000/hour = 1.4/sec) |
| **Website scraping** | 10-20 | Balance speed vs politeness |
| **Disk I/O** | 2-4 | Limited by disk speed |

## Testing Strategy

### Test Correctness

```python
def test_parallel_vs_serial():
    """Ensure parallel produces same results as serial"""
    items = list(range(100))

    # Serial
    serial_result = [process(item) for item in items]

    # Parallel
    scraper = ParallelScraper(max_workers=10)
    parallel_result = scraper.process_parallel(items, process)

    assert len(serial_result) == len(parallel_result)

    for s, p in zip(serial_result, parallel_result):
        assert s == p
```

### Test Performance

```python
import time

def benchmark_speedup():
    """Measure parallel speedup"""
    items = list(range(274))

    # Serial
    start = time.time()
    serial_result = [process(item) for item in items]
    serial_time = time.time() - start

    # Parallel
    scraper = ParallelScraper(max_workers=10)
    start = time.time()
    parallel_result = scraper.process_parallel(items, process)
    parallel_time = time.time() - start

    speedup = serial_time / parallel_time

    print(f"Serial: {serial_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x")

    assert speedup > 5  # Expect at least 5x speedup
```

## Benefits

| Benefit | Impact |
|---------|--------|
| **10-21x faster** | From hours to minutes |
| **Better resource use** | Utilize multiple cores |
| **Scalability** | Handle larger datasets |
| **User experience** | Faster feedback |

## Related Issues

- Issue #002: GitHub Token Management
- Issue #006: No Caching Mechanism
- Issue #009: Performance Optimization

## References

- [concurrent.futures Documentation](https://docs.python.org/3/library/concurrent.futures.html)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [Python Async IO Guide](https://docs.python.org/3/library/asyncio.html)
- [GitHub API Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)

---

**Assigned To**: TBD
**Due Date**: 2026-02-13 (Lower Priority - Performance Enhancement)
**Dependencies**: None
