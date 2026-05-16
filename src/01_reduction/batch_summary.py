#!/usr/bin/env python3
"""Generate a summary CSV for completed pipeline batches.

Usage:
    python src/01_reduction/batch_summary.py --batch 1 --clusters Abell_0068 Abell_0611 MACSJ0429.6-0253
    python src/01_reduction/batch_summary.py --batch all
"""
import argparse
import csv
import glob
import os
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_DIR / "chandra_data_evt"
OUTPUT_DIR = PROJECT_DIR / "output" / "products" / "pipeline"


def summarize_cluster(cluster: str) -> dict:
    """Collect key metrics for one cluster."""
    cdir = DATA_DIR / cluster
    processed = cdir / "processed"
    row = {
        "cluster": cluster,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    # Count ObsIDs
    raw = cdir / "raw"
    obsids = [d.name for d in raw.iterdir() if d.is_dir()] if raw.exists() else []
    row["n_obsids"] = len(obsids)

    # Check repro
    repro_ok = 0
    for oid in obsids:
        repro_evt2 = glob.glob(str(cdir / "raw" / oid / "repro" / "*repro_evt2*"))
        if repro_evt2:
            repro_ok += 1
    row["repro_done"] = repro_ok
    row["repro_total"] = len(obsids)

    # Check pipeline outputs
    for key, fname in [
        ("has_merged_evt", "merged_evt.fits"),
        ("has_merged_clean_evt", "merged_clean_evt.fits"),
        ("has_src", "src.fits"),
        ("has_broad_flux", "broad_flux.img"),
        ("has_flux_clean", "clean_fluxed/flux_clean.img"),
        ("has_flux_csmooth", "clean_fluxed/flux_csmooth.img"),
    ]:
        fpath = processed / fname
        row[key] = "yes" if fpath.exists() else "no"
        if fpath.exists():
            row[key + "_size_mb"] = round(fpath.stat().st_size / 1e6, 1)
        else:
            row[key + "_size_mb"] = ""

    # Count detected point sources
    src_fits = processed / "src.fits"
    if src_fits.exists():
        try:
            from astropy.io import fits
            with fits.open(src_fits) as hdul:
                row["n_point_sources"] = len(hdul[1].data)
        except Exception:
            row["n_point_sources"] = "?"
    else:
        row["n_point_sources"] = ""

    # Overall status
    required = ["has_merged_evt", "has_src", "has_flux_clean"]
    row["pipeline_status"] = "done" if all(row.get(k) == "yes" for k in required) else "incomplete"

    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", required=True, help="Batch number or 'all'")
    parser.add_argument("--clusters", nargs="+", help="Cluster names (required unless --batch all)")
    args = parser.parse_args()

    if args.batch == "all":
        clusters = sorted(d.name for d in DATA_DIR.iterdir() if d.is_dir() and (d / "processed").exists())
        batch_label = "all"
    else:
        clusters = args.clusters or []
        batch_label = args.batch

    if not clusters:
        print("No clusters to summarize.")
        return

    rows = []
    for c in clusters:
        print(f"Summarizing {c}...")
        rows.append(summarize_cluster(c))

    outpath = OUTPUT_DIR / f"batch_{batch_label}_summary.csv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with outpath.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {outpath} ({len(rows)} clusters)")
    for r in rows:
        print(f"  {r['cluster']}: {r['pipeline_status']} (repro {r['repro_done']}/{r['repro_total']}, {r['n_point_sources']} src)")


if __name__ == "__main__":
    main()
