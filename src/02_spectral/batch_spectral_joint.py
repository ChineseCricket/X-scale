#!/usr/bin/env python3
"""Batch run spectral fitting with beta-model correction for all 23 clusters."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from postproces_cluster import (
    load_cluster_configs_from_table,
    resolve_cluster_config,
    default_cluster_dir,
    angular_radius_arcsec,
    compute_r500_mpc,
    CLUSTER_TABLE_PATH,
)

DEFAULT_H0 = 70.0
DEFAULT_OMEGA_M = 0.3
SUMMARY_CSV = Path("output/products/spectral/spectral_joint_summary.csv")
SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)


def load_accept_reference(path: str = "configs/accept_reference.csv") -> dict:
    """Load ACCEPT reference T_X values."""
    ref = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            ref[row["cluster_key"]] = dict(row)
    return ref


def get_r500(config_key, config):
    """Compute R500 for a cluster."""
    m500_raw = config.m500
    redshift = config.redshift
    h = DEFAULT_H0 / 100.0
    m500_msun = m500_raw / h if config.m500_h_inverse else m500_raw
    return angular_radius_arcsec(
        compute_r500_mpc(m500_msun, redshift, DEFAULT_H0, DEFAULT_OMEGA_M),
        redshift, DEFAULT_H0, DEFAULT_OMEGA_M,
    )


def run_cluster(cluster_key, config):
    """Run spectral fitting for one cluster. Returns dict of results."""
    result = {
        "cluster_key": cluster_key,
        "z": config.redshift,
        "r500_arcsec": get_r500(cluster_key, config),
        "status": "pending",
    }
    try:
        proc = subprocess.run(
            ["python", str(Path(__file__).parent / "fit_spectral_joint.py"),
             "--cluster", cluster_key],
            capture_output=True, text=True, timeout=600,
        )
        stdout = proc.stdout + "\n" + proc.stderr
        # Extract T_X from output
        for line in stdout.split("\n"):
            if "T_X" in line and "keV" in line:
                parts = line.split()
                for j, p in enumerate(parts):
                    if p == "=":
                        result["Tx_keV"] = float(parts[j + 1])
                    if "rstat" in line.lower():
                        for j, p in enumerate(parts):
                            if p == "=":
                                result["rstat"] = float(parts[j + 1])
            if "Abundance" in line and "solar" in line:
                parts = line.split()
                for j, p in enumerate(parts):
                    if p == "=":
                        result["abundance"] = float(parts[j + 1])
            if "Correction factor" in line:
                parts = line.split()
                for j, p in enumerate(parts):
                    if p == "=":
                        result["correction_factor"] = float(parts[j + 1])

        # Try to read JSON result
        cluster_dir = default_cluster_dir(cluster_key, config)
        json_path = cluster_dir / "postprocess_r500" / f"{cluster_key}_correction_results.json"
        if json_path.exists():
            with open(json_path) as f:
                d = json.load(f)
            result["Tx_keV"] = d.get("temperature_keV")
            result["Tx_err_lo"] = d.get("confidence", {}).get("icm.kT", {}).get("lo")
            result["Tx_err_hi"] = d.get("confidence", {}).get("icm.kT", {}).get("hi")
            result["rstat"] = d.get("rstat")
            result["statval"] = d.get("statval")
            result["dof"] = d.get("dof")
            result["abundance"] = d.get("abundance_solar")
            result["n_spectra"] = d.get("n_spectra")
            result["R_EM"] = d.get("R_EM")
        result["status"] = "done"
    except Exception as exc:
        result["status"] = f"failed: {exc}"
    return result


def main():
    configs = load_cluster_configs_from_table(CLUSTER_TABLE_PATH)
    accept = load_accept_reference()

    # Filter to 23 pipeline clusters
    with open("memory/pipeline_status.csv") as f:
        pipeline = list(csv.DictReader(f))
    pipeline_clusters = [row["cluster_key"] for row in pipeline
                         if row.get("pipeline") == "done" and row.get("spectral") in ("pending", "tested")]

    print(f"[info] Running {len(pipeline_clusters)} clusters with β-model correction...")

    results = []
    for i, key in enumerate(pipeline_clusters):
        if key not in configs:
            print(f"[warn] {key}: missing from config table, skipping")
            continue
        cfg = configs[key]
        print(f"\n[{i+1}/{len(pipeline_clusters)}] {key} (z={cfg.redshift:.3f})")
        r = run_cluster(key, cfg)
        accept_tx = accept.get(key, {}).get("accept_tx_kev", "N/A")
        try:
            r["accept_Tx"] = float(accept_tx)
        except (ValueError, TypeError):
            r["accept_Tx"] = None
        if r.get("Tx_keV") and r.get("accept_Tx"):
            r["ratio"] = r["Tx_keV"] / r["accept_Tx"]
        results.append(r)
        if r.get("Tx_keV"):
            print(f"  T_X = {r['Tx_keV']:.2f} keV (ACCEPT={r.get('accept_Tx', '?')}), rstat={r.get('rstat', '?')}")

    # Write summary
    if results:
        fieldnames = list(results[0].keys())
        with open(SUMMARY_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"\n[info] Summary: {SUMMARY_CSV}")

        # Quick stats
        good = [r for r in results if r.get("ratio")
                and 0.7 <= r["ratio"] <= 1.3
                and r.get("rstat") and r["rstat"] < 1.5]
        acceptable = [r for r in results if r.get("ratio")
                      and 0.5 <= r["ratio"] <= 1.5
                      and r.get("rstat")]
        print(f"\n  Good (0.7<ratio<1.3, rstat<1.5): {len(good)}/{len(results)}")
        print(f"  Acceptable (0.5<ratio<1.5): {len(acceptable)}/{len(results)}")


if __name__ == "__main__":
    main()
