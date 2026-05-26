#!/usr/bin/env python3
"""Batch wrapper for the Phase-3 B+C spectral fitting method."""
from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CLUSTER_TABLE = PROJECT_DIR / "cluster_center_table.csv"
DEFAULT_DATA_ROOT = PROJECT_DIR / "chandra_data"
DEFAULT_SCRIPT = Path(__file__).resolve().parent / "fit_spectral_joint.py"


def read_cluster_keys(path: Path) -> list[str]:
    with path.open(newline="") as f:
        return [row["cluster_key"] for row in csv.DictReader(f)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster-table", type=Path, default=DEFAULT_CLUSTER_TABLE)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--clusters", nargs="*", help="Cluster keys to run; default reads all keys from table")
    parser.add_argument("--resume", action="store_true", help="Skip repro/imaging/blanksky/specextract and rerun only beta/Sherpa/summary")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    keys = args.clusters or read_cluster_keys(args.cluster_table)
    for key in keys:
        cluster_dir = args.data_root / key
        cmd = [
            "python",
            str(DEFAULT_SCRIPT),
            "--cluster-key",
            key,
            "--cluster-dir",
            str(cluster_dir),
            "--cluster-table",
            str(args.cluster_table),
        ]
        if args.resume:
            cmd += ["--no-run-repro", "--no-run-imaging", "--no-run-blanksky", "--no-run-specextract"]
        print("+ " + " ".join(cmd))
        if not args.dry_run:
            subprocess.run(cmd, cwd=str(PROJECT_DIR), check=True)


if __name__ == "__main__":
    main()
