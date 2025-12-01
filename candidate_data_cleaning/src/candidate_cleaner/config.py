from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class StatusMapping:
    source: str
    target: Optional[str]


@dataclass
class FieldRule:
    column: str
    required: bool = False
    alias: Optional[str] = None
    normalize: Optional[str] = None


@dataclass
class OutputConfig:
    cleaned_filename: str = "candidate_cleaned.xlsx"
    issues_filename: str = "candidate_issues.xlsx"
    report_filename: str = "candidate_cleaning_report.json"


@dataclass
class PipelineConfig:
    status_mappings: List[StatusMapping]
    field_rules: List[FieldRule]
    primary_key: List[str] = field(default_factory=lambda: ["name", "phone"])
    phone_column: str = "phone"
    name_column: str = "name"
    timestamp_columns: List[str] = field(default_factory=list)
    source_file_column: str = "source_file"
    batch_id: Optional[str] = None
    source_filename: Optional[str] = None
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(path: Path) -> PipelineConfig:
    with path.open("r", encoding="utf-8") as fp:
        payload = yaml.safe_load(fp)

    output = payload.get("output", {})
    status_mappings = [
        StatusMapping(source=item["source"], target=item.get("target"))
        for item in payload.get("status_mappings", [])
    ]
    field_rules = [
        FieldRule(
            column=item["column"],
            required=item.get("required", False),
            alias=item.get("alias"),
            normalize=item.get("normalize"),
        )
        for item in payload.get("field_rules", [])
    ]

    config = PipelineConfig(
        status_mappings=status_mappings,
        field_rules=field_rules,
        primary_key=payload.get("primary_key", ["name", "phone"]),
        phone_column=payload.get("phone_column", "phone"),
        name_column=payload.get("name_column", "name"),
        timestamp_columns=payload.get("timestamp_columns", []),
        source_file_column=payload.get("source_file_column", "source_file"),
        batch_id=payload.get("batch_id"),
        source_filename=payload.get("source_filename"),
        output=OutputConfig(**output),
    )
    return config
