from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .config import PipelineConfig
from .transformers import NORMALIZERS


@dataclass
class IssueRecord:
    reason: str
    rows: pd.DataFrame


@dataclass
class CleanResult:
    cleaned: pd.DataFrame
    issues: List[IssueRecord]
    summary: Dict[str, int]


def _status_lookup(config: PipelineConfig) -> Dict[str, Optional[str]]:
    return {item.source: item.target for item in config.status_mappings}


def _annotate_issue(rows: pd.DataFrame, reason: str) -> IssueRecord:
    if rows.empty:
        return IssueRecord(reason=reason, rows=rows)
    annotated = rows.copy()
    annotated.insert(0, "row_index", annotated.index)
    annotated["issue_reason"] = reason
    return IssueRecord(reason=reason, rows=annotated.reset_index(drop=True))


def normalize_columns(df: pd.DataFrame, config: PipelineConfig) -> Tuple[pd.DataFrame, List[IssueRecord]]:
    work_df = df.copy().reset_index(drop=True)
    issues: List[IssueRecord] = []

    alias_map = {
        rule.alias: rule.column
        for rule in config.field_rules
        if rule.alias and rule.alias in work_df.columns
    }
    if alias_map:
        work_df.rename(columns=alias_map, inplace=True)

    for rule in config.field_rules:
        if rule.column not in work_df.columns:
            work_df[rule.column] = pd.NA

        normalizer = NORMALIZERS.get(rule.normalize or "")
        if normalizer:
            work_df[rule.column] = work_df[rule.column].apply(normalizer)

        if rule.required:
            missing_mask = work_df[rule.column].isna() | (work_df[rule.column] == "")
            if missing_mask.any():
                issue_rows = work_df.loc[missing_mask]
                issues.append(_annotate_issue(issue_rows, f"missing_{rule.column}"))

    for col in work_df.select_dtypes(include="object").columns:
        work_df[col] = work_df[col].astype(str).str.strip()

    phone_col = config.phone_column
    normalized_phone_col = f"{phone_col}_normalized"
    if phone_col in work_df.columns and normalized_phone_col not in work_df.columns:
        work_df[normalized_phone_col] = work_df[phone_col]

    return work_df, issues


def map_status(df: pd.DataFrame, config: PipelineConfig) -> IssueRecord:
    lookup = _status_lookup(config)
    status_col = "status"
    if status_col not in df.columns:
        return IssueRecord(reason="status_missing_column", rows=pd.DataFrame())

    mapped = []
    issue_labels = []
    for value in df[status_col]:
        if pd.isna(value) or str(value).strip() == "":
            mapped.append(None)
            issue_labels.append("missing_status")
            continue
        raw = str(value).strip()
        mapped_value = lookup.get(raw)
        if mapped_value:
            mapped.append(mapped_value)
            issue_labels.append(None)
        else:
            mapped.append(None)
            issue_labels.append("status_unmapped")

    df["status_mapped"] = mapped
    reason_series = pd.Series(issue_labels, index=df.index)
    issue_mask = reason_series.notna()
    issue_rows = df.loc[issue_mask]
    if issue_rows.empty:
        return IssueRecord(reason="status", rows=pd.DataFrame())
    annotated = issue_rows.copy()
    annotated.insert(0, "row_index", annotated.index)
    annotated["issue_reason"] = reason_series[issue_mask].values
    return IssueRecord(reason="status", rows=annotated.reset_index(drop=True))


def deduplicate(df: pd.DataFrame, config: PipelineConfig) -> Tuple[pd.DataFrame, IssueRecord]:
    pk_cols = config.primary_key
    if not pk_cols:
        return df.reset_index(drop=True), IssueRecord(reason="duplicates", rows=pd.DataFrame())

    sort_cols = [col for col in config.timestamp_columns if col in df.columns]
    df_sorted = df.sort_values(by=sort_cols, ascending=False).reset_index(drop=True) if sort_cols else df.copy()

    dup_mask = df_sorted.duplicated(subset=pk_cols, keep="first")
    dup_rows = df_sorted.loc[dup_mask]
    return df_sorted.loc[~dup_mask].reset_index(drop=True), _annotate_issue(dup_rows, "duplicate_primary_key")


def aggregate_issues(issues: List[IssueRecord]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for issue in issues:
        summary[f"issue_{issue.reason}"] = summary.get(f"issue_{issue.reason}", 0) + len(issue.rows)
    return summary


def run_cleaning(df: pd.DataFrame, config: PipelineConfig) -> CleanResult:
    normalized_df, issues = normalize_columns(df, config)

    deduped_df, duplicate_issue = deduplicate(normalized_df, config)
    issues.append(duplicate_issue)

    status_issue = map_status(deduped_df, config)
    issues.append(status_issue)

    phone_col = f"{config.phone_column}_normalized"
    cleaned = deduped_df.loc[deduped_df[phone_col].notna()].reset_index(drop=True)

    summary = {
        "total_rows": int(len(normalized_df)),
        "post_dedup_rows": int(len(deduped_df)),
        "cleaned_rows": int(len(cleaned)),
    }
    summary.update(aggregate_issues(issues))

    return CleanResult(cleaned=cleaned, issues=issues, summary=summary)


def write_outputs(result: CleanResult, config: PipelineConfig, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    cleaned_path = output_dir / config.output.cleaned_filename
    issues_path = output_dir / config.output.issues_filename
    report_path = output_dir / config.output.report_filename

    result.cleaned.to_excel(cleaned_path, index=False)

    issue_frames = [issue.rows for issue in result.issues if not issue.rows.empty]
    if issue_frames:
        pd.concat(issue_frames, ignore_index=True).to_excel(issues_path, index=False)

    with report_path.open("w", encoding="utf-8") as fp:
        json.dump(result.summary, fp, ensure_ascii=False, indent=2)
