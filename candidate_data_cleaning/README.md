# Candidate Data Cleaning Toolkit

This project provides a reusable pipeline to clean and prepare candidate datasets before importing them into the headhunter collaboration platform. It focuses on:

- Normalizing key identifiers (phone, email, candidate name)
- Deduplicating records while preserving the latest updates
- Validating and mapping candidate status values
- Exporting clean datasets, exception reports, and audit summaries

## Project Layout

- `src/candidate_cleaner/`: Python package with the core cleaning logic and CLI entrypoints
- `tests/`: Unit and data-contract tests for the cleaning rules
- `notebooks/`: Exploratory analysis or ad-hoc validation notebooks
- `configs/`: YAML/JSON templates to configure field mappings and business rules
- `data/`: Input and output sample datasets (git-ignored)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m candidate_cleaner.clean_cli --config configs/default.yaml \
  --input ../candidate\ 2025-09-26\ 13_28_27.xls
```

The command above reads the raw XLS export, applies the configured cleaning rules, and stores cleaned data plus issue reports under `data/outputs/`.

## Next Steps

- Fill in `configs/default.yaml` with the status mapping and field requirements
- Implement the cleaning pipeline in `candidate_cleaner/clean_pipeline.py`
- Add unit tests for status mapping, phone normalization, and dedupe behaviour
- Integrate the project with the headhunter platform ingestion workflow once validated

