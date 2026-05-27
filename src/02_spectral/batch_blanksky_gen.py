#!/usr/bin/env python3
"""Batch generate blank-sky event files and extract spectra for all 23 clusters.

Run BEFORE batch_spectral_xrb.py. This step is separate because:
1. blanksky can fail if CALDB files are missing for certain ObsIDs
2. specextract can be slow (especially for multi-ObsID clusters)
3. Separating generation from fitting allows retrying individual failures
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from postproces_cluster import (
    CLUSTER_TABLE_PATH,
    angular_radius_arcsec,
    compute_r500_mpc,
    default_cluster_dir,
    discover_individual_evt2,
    find_xray_peak_center,
    load_cluster_configs_from_table,
    load_point_source_masks,
    obsid_from_evt_path,
    resolve_cluster_config,
)
from fit_spectral_xrb import (
    DEFAULT_ANNULUS_INNER_R500,
    DEFAULT_ANNULUS_OUTER_R500,
    DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX,
    DEFAULT_POINT_SOURCE_RADIUS_SCALE,
    DEFAULT_POINT_SOURCE_SIGMA_MIN,
    DEFAULT_POINT_SOURCE_SKIP_CENTER_R500,
    DEFAULT_SOURCE_OUTER_R500,
    DEFAULT_XRAY_PEAK_SEARCH_ARCSEC,
    extract_joint_spectra,
    load_existing_blanksky,
    run_blanksky_for_obsids,
)

H0 = 70.0
OMEGA_M = 0.3


def main():
    configs = load_cluster_configs_from_table(CLUSTER_TABLE_PATH)
    with open("memory/pipeline_status.csv") as f:
        pipeline = list(csv.DictReader(f))
    pipeline_clusters = [
        row["cluster_key"] for row in pipeline
        if row.get("pipeline") == "done"
    ]

    print(f"[info] Processing {len(pipeline_clusters)} clusters for blank-sky generation")
    results = []

    for i, key in enumerate(pipeline_clusters, 1):
        if key not in configs:
            print(f"[warn] {key}: missing from config table")
            continue
        cfg = configs[key]
        _, config = resolve_cluster_config(key, configs)

        redshift = config.redshift
        m500_raw = config.m500
        if redshift is None or m500_raw is None:
            print(f"[warn] {key}: missing z or M500")
            continue

        h = H0 / 100.0
        m500_msun = m500_raw / h if config.m500_h_inverse else m500_raw
        r500_mpc = compute_r500_mpc(m500_msun, redshift, H0, OMEGA_M)
        r500_arcsec = angular_radius_arcsec(r500_mpc, redshift, H0, OMEGA_M)

        cluster_dir = default_cluster_dir(key, config)
        if cluster_dir is None:
            print(f"[warn] {key}: no data directory")
            continue
        cluster_dir = cluster_dir.resolve()

        print(f"\n[{i}/{len(pipeline_clusters)}] {key} (z={redshift:.3f}, R500={r500_arcsec:.0f}\")")

        evt2_list = discover_individual_evt2(cluster_dir)
        if not evt2_list:
            print(f"  [skip] No evt2 files")
            results.append({"cluster": key, "status": "no_evt2"})
            continue
        evt2_by_obsid = {obsid_from_evt_path(e): e for e in evt2_list}
        print(f"  ObsIDs: {sorted(evt2_by_obsid.keys())}")

        outdir = cluster_dir / "processed_joint_bxc"

        # Check existing blank-sky
        existing = load_existing_blanksky(evt2_by_obsid, outdir / "blanksky", cluster_dir, key)
        if len(existing) == len(evt2_by_obsid):
            print(f"  [skip] All blank-sky files already exist")
        else:
            t0 = time.time()
            blank_by_obsid = run_blanksky_for_obsids(evt2_by_obsid, outdir / "blanksky")
            dt = time.time() - t0
            print(f"  Generated {len(blank_by_obsid)}/{len(evt2_by_obsid)} blank-sky files ({dt:.0f}s)")

            if len(blank_by_obsid) < len(evt2_by_obsid):
                print(f"  [warn] Some ObsIDs failed blanksky generation")

        # Extract spectra
        flux_image = None
        for p in [
            cluster_dir / "processed" / "clean_fluxed" / "flux_clean.img",
            cluster_dir / "processed" / "broad_flux.img",
        ]:
            if p.exists():
                flux_image = p
                break

        peak = find_xray_peak_center(flux_image, config.center_ra, config.center_dec, DEFAULT_XRAY_PEAK_SEARCH_ARCSEC)
        center_ra = peak[0] if peak else config.center_ra
        center_dec = peak[1] if peak else config.center_dec

        src_catalog = None
        for p in [cluster_dir / "processed" / "src.fits"]:
            if p.exists():
                src_catalog = str(p)
                break

        masks = load_point_source_masks(
            cluster_dir, src_catalog, center_ra, center_dec, r500_arcsec,
            DEFAULT_ANNULUS_OUTER_R500,
            DEFAULT_POINT_SOURCE_SIGMA_MIN,
            DEFAULT_POINT_SOURCE_RADIUS_SCALE,
            DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX,
            DEFAULT_POINT_SOURCE_SKIP_CENTER_R500,
        )

        # Load existing blanksky for extraction
        blank_by_obsid = load_existing_blanksky(evt2_by_obsid, outdir / "blanksky", cluster_dir, key)
        if not blank_by_obsid:
            print(f"  [skip] No blank-sky files for extraction")
            results.append({"cluster": key, "status": "no_blanksky"})
            continue

        t0 = time.time()
        spectrum_sets = extract_joint_spectra(
            cluster_dir, outdir, key, evt2_by_obsid, blank_by_obsid,
            center_ra, center_dec, r500_arcsec, masks,
            run_specextract=True,
        )
        dt = time.time() - t0
        n_src = sum(1 for s in spectrum_sets if s.source_pi)
        n_ann = sum(1 for s in spectrum_sets if s.annulus_pi)
        print(f"  Extracted spectra: {n_src} source, {n_ann} annulus ({dt:.0f}s)")

        results.append({
            "cluster": key,
            "status": "done",
            "n_obsids": len(evt2_by_obsid),
            "n_blanksky": len(blank_by_obsid),
            "n_source_spectra": n_src,
            "n_annulus_spectra": n_ann,
        })

    # Summary
    done = sum(1 for r in results if r["status"] == "done")
    print(f"\n{'='*50}")
    print(f"  {done}/{len(results)} clusters completed successfully")
    for r in results:
        if r["status"] != "done":
            print(f"  [fail] {r['cluster']}: {r['status']}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
