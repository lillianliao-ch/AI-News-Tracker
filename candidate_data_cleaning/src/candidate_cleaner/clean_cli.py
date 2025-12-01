from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from .config import PipelineConfig, load_config
from .pipeline import run_cleaning, write_outputs

app = typer.Typer(add_completion=False)
console = Console()


def _print_summary(summary: dict[str, int]) -> None:
    table = Table(title="Cleaning Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for key, value in summary.items():
        table.add_row(key, str(value))
    console.print(table)


@app.command()
def clean(
    input_path: Path = typer.Option(..., exists=True, help="Path to the raw candidate XLS/XLSX/CSV file"),
    config_path: Path = typer.Option(..., exists=True, help="Path to YAML configuration file"),
    output_dir: Path = typer.Option(Path("data/outputs"), help="Directory to store cleaned files"),
) -> None:
    console.log(f"Loading config from {config_path}")
    config = load_config(config_path)

    console.log(f"Reading input dataset {input_path}")
    if input_path.suffix.lower() in {".xls", ".xlsx"}:
        df = pd.read_excel(input_path)
    else:
        df = pd.read_csv(input_path)

    if config.source_file_column:
        df[config.source_file_column] = input_path.name
    if config.batch_id:
        df["import_batch_id"] = config.batch_id

    result = run_cleaning(df, config)
    write_outputs(result, config, output_dir)

    _print_summary(result.summary)
    console.log(f"Cleaned data written to {output_dir}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
