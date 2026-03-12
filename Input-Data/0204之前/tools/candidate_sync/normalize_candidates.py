#!/usr/bin/env python3
import argparse
import json
import math
import os
from datetime import datetime, timezone

import pandas as pd
import yaml
from dateutil import parser as dtparser


def load_yaml(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def to_datetime_iso(value, tz: str | None = None) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        dt = dtparser.parse(str(value), dayfirst=False)
        if tz:
            try:
                import zoneinfo

                dt = dt.astimezone(zoneinfo.ZoneInfo(tz))
            except Exception:
                dt = dt.astimezone(timezone.utc)
        else:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return None


def last_activity_bucket(iso_str: str | None) -> str:
    if not iso_str:
        return 'unknown'
    try:
        dt = dtparser.isoparse(iso_str)
        now = datetime.now(dt.tzinfo or timezone.utc)
        days = (now - dt).days
        if days < 90:
            return 'lt_90d'
        if days < 180:
            return 'd90_180'
        if days < 365:
            return 'd180_365'
        return 'gt_365d'
    except Exception:
        return 'unknown'


def normalize_phone(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    # Keep leading '+' and digits only
    cleaned = []
    for i, ch in enumerate(value):
        if ch.isdigit() or (ch == '+' and i == 0):
            cleaned.append(ch)
    result = ''.join(cleaned)
    return result if result else None


def split_array(value: str | None, delimiter: str = ';') -> list[str] | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if not isinstance(value, str):
        value = str(value)
    items = [x.strip() for x in value.split(delimiter) if x.strip()]
    if not items:
        return None
    # lower and dedup while preserving order
    seen = set()
    out: list[str] = []
    for it in items:
        low = it.lower()
        if low not in seen:
            seen.add(low)
            out.append(low)
    return out


def apply_transforms(series: pd.Series, transforms: list[str] | None, options: dict) -> pd.Series:
    if not transforms:
        return series
    tz = options.get('timezone')
    delimiter = options.get('array_delimiter', ';')

    def _transform(x):
        val = x
        for t in transforms:
            if val is None or (isinstance(val, float) and math.isnan(val)):
                break
            if t == 'trim':
                val = str(val).strip()
            elif t == 'lowercase':
                val = str(val).lower()
            elif t == 'to_datetime':
                val = to_datetime_iso(val, tz)
            elif t == 'strip_non_digits_keep_plus':
                val = normalize_phone(str(val))
            elif t in ('split_semicolon', 'split'):
                val = split_array(str(val), delimiter)
            elif t == 'trim_items':
                if isinstance(val, list):
                    val = [v.strip() for v in val]
            elif t == 'dedup':
                if isinstance(val, list):
                    seen = set()
                    new = []
                    for v in val:
                        if v not in seen:
                            seen.add(v)
                            new.append(v)
                    val = new
            # else: ignore unknown transform
        return val

    return series.map(_transform)


def normalize_frame(df: pd.DataFrame, mapping: dict, schema: dict) -> pd.DataFrame:
    fields = schema.get('fields', {})
    dedup = schema.get('dedup_strategy', {})
    options = mapping.get('options', {})
    mappings = mapping.get('mappings', [])

    out = pd.DataFrame()

    # Map columns
    for m in mappings:
        src = m['source']
        tgt = m['target']
        transforms = m.get('transforms')
        if src not in df.columns:
            continue
        col = df[src]
        col = apply_transforms(col, transforms, options)
        out[tgt] = col

    # Derive last_activity_bucket
    if 'last_activity_at' in out.columns:
        out['last_activity_bucket'] = out['last_activity_at'].map(last_activity_bucket)

    # Ensure all schema fields exist
    for f in fields.keys():
        if f not in out.columns:
            out[f] = None

    # Dedup
    keep = dedup.get('keep', 'first')
    subset_candidates = dedup.get('primary_keys', []) + [
        '_join_'.join(fb) if isinstance(fb, list) else fb for fb in dedup.get('fallbacks', [])
    ]

    # Build helper composite columns for fallbacks
    for fb in dedup.get('fallbacks', []):
        if isinstance(fb, list):
            name = '_join_'.join(fb)
            out[name] = out[fb].astype(str).agg('|'.join, axis=1)

    deduped = out.copy()
    for key in subset_candidates:
        if not key:
            continue
        if key not in deduped.columns:
            continue
        # Drop NAs in key to avoid collapsing rows with missing identifiers
        subset = deduped[~deduped[key].isna()]
        if subset.empty:
            continue
        idx = subset.drop_duplicates(subset=[key], keep=keep).index
        deduped = deduped.loc[idx].copy()

    # Clean helper columns
    for fb in dedup.get('fallbacks', []):
        if isinstance(fb, list):
            name = '_join_'.join(fb)
            if name in deduped.columns:
                deduped.drop(columns=[name], inplace=True)

    # Heuristic confidence
    coverage_cols = [
        'email', 'phone', 'current_title', 'current_company', 'skills', 'city',
        'last_activity_at', 'status'
    ]
    def _confidence(row) -> float:
        filled = sum(1 for c in coverage_cols if pd.notna(row.get(c)))
        return round(filled / max(len(coverage_cols), 1), 3)

    deduped['data_confidence_score'] = deduped.apply(_confidence, axis=1)

    return deduped


def main():
    parser = argparse.ArgumentParser(description='Normalize exported candidate CSVs to a standard schema')
    parser.add_argument('--input', required=True, help='Path to exported CSV file')
    parser.add_argument('--mapping', required=True, help='Path to mapping YAML')
    parser.add_argument('--schema', required=True, help='Path to schema YAML')
    parser.add_argument('--out', required=True, help='Output CSV path')
    parser.add_argument('--parquet', default=None, help='Optional Parquet output path')
    parser.add_argument('--encoding', default='utf-8-sig', help='CSV encoding (default utf-8-sig)')
    parser.add_argument('--delimiter', default=',', help='CSV delimiter (default ,)')

    args = parser.parse_args()

    src = pd.read_csv(args.input, encoding=args.encoding, delimiter=args.delimiter)
    mapping = load_yaml(args.mapping)
    schema = load_yaml(args.schema)

    normalized = normalize_frame(src, mapping, schema)

    # Arrays to semicolon-joined strings for CSV
    def _to_csv_cell(v):
        if isinstance(v, list):
            return ';'.join([str(x) for x in v])
        return v

    csv_df = normalized.applymap(_to_csv_cell)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    csv_df.to_csv(args.out, index=False, encoding='utf-8')

    if args.parquet:
        try:
            os.makedirs(os.path.dirname(args.parquet), exist_ok=True)
            normalized.to_parquet(args.parquet, index=False)
        except Exception as e:
            print(f"Warning: failed to write parquet: {e}")

    print(f"Wrote CSV: {args.out}")
    if args.parquet:
        print(f"Wrote Parquet: {args.parquet}")


if __name__ == '__main__':
    main()


