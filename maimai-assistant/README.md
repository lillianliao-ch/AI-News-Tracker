# Maimai Assistant

Chrome extension for Maimai recruiting workflows. It combines candidate-side collection/interaction helpers with a job-poster panel that pulls data from `personal-ai-headhunter`.

## Current Scope

- Candidate-side assistance on supported Maimai recruiting, search, IM, and profile pages
- Batch-style operations such as friend requests, messaging support, extraction, export, and local stats
- CRM-like side panel for richer candidate context and backend-connected actions
- Job-posting helper on Maimai position create/edit pages using backend job data

## Runtime Targets

Current manifest targets include:

- `https://maimai.cn/ent/v41/recruit/*`
- `https://maimai.cn/ent/v41/groups*`
- `https://maimai.cn/ent/v41/im*`
- `https://maimai.cn/web/search_center*`
- `https://maimai.cn/profile/detail*`
- `https://maimai.cn/contact/*`
- `https://maimai.cn/card/*`
- `https://maimai.cn/ent/v41/positions/add*`
- `https://maimai.cn/ent/v41/positions/edit*`

## Installation

1. Open Chrome and visit `chrome://extensions/`
2. Enable Developer Mode
3. Click “Load unpacked”
4. Select the [extension](extension) directory

## Read Order

1. [docs/INDEX.md](docs/INDEX.md)
2. [docs/crm-design-spec.md](docs/crm-design-spec.md)
3. [extension/manifest.json](extension/manifest.json)

## Code Map

- [extension/manifest.json](extension/manifest.json): content-script targets and extension entrypoints
- [extension/content](extension/content): candidate-side extraction, panel logic, IM processing
- [extension/search](extension/search): search-specific parsing logic
- [extension/job-poster](extension/job-poster): job-posting helper UI and autofill logic
- [extension/background](extension/background): storage, exports, proxy fetch, resume download handling
- [extension/popup](extension/popup): popup configuration and quick actions

## Backend Coupling

This project is partially standalone:

- basic scraping/export works as a browser extension
- richer CRM actions and job posting rely on `personal-ai-headhunter`, usually at `http://localhost:8502`

## Source Of Truth

- Runtime behavior: [extension/manifest.json](extension/manifest.json) plus code under [extension](extension)
- Design intent for the CRM panel: [docs/crm-design-spec.md](docs/crm-design-spec.md)
