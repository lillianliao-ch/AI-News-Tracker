Candidate CSV Normalization (SaaS export → standardized schema)

Steps
1) Export a CSV from your SaaS with columns similar to the example mapping.
2) Install deps:
   
   pip install -r requirements.txt

3) Run normalization:
   
   python normalize_candidates.py \
     --input exported_candidates.csv \
     --mapping mapping.example.yaml \
     --schema schema.yaml \
     --out out/normalized_candidates.csv \
     --parquet out/normalized_candidates.parquet

Notes
- Arrays (skills, tags) are semicolon-separated in the CSV output; Parquet preserves list types.
- Dedup order: candidate_id → email → phone → (full_name + current_company), keep first.
- last_activity_bucket is derived as: <90d, 90–180d, 180–365d, >365d.
- Adjust mapping.example.yaml to match your SaaS headers.

Privacy & Compliance
- Only process data you’re authorized to export.
- Store PII encrypted and apply frequency capping/opt-out when messaging.

