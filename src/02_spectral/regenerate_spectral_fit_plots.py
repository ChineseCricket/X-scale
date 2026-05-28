#!/usr/bin/env python3
"""Regenerate background-aware spectral fit plots from saved Phase 3 JSONs.

The WSTAT fits use blank-sky PHA files as particle backgrounds. Sherpa's raw
data plot shows source-region counts before that blank-sky estimate is removed,
which can make the folded source model look systematically low. This script
rebuilds the saved model and makes a QA figure whose primary comparison is
background-subtracted/net data versus the folded source model.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np


RESULTS_DIR = Path("output/products/spectral")
FIGURE_DIR = Path("output/figures/spectral")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--figdir", type=Path, default=FIGURE_DIR)
    parser.add_argument("--cluster", action="append", default=[], help="Optional cluster key; repeatable.")
    parser.add_argument("--suffix", default="_fit.png", help="Output filename suffix.")
    return parser.parse_args()


def as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def configure_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-codex")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def load_result_paths(results_dir: Path, clusters: list[str]) -> list[Path]:
    if clusters:
        paths = []
        for cluster in clusters:
            slug = cluster.replace(".", "_").replace("-", "_").replace("+", "_")
            candidates = [results_dir / f"{cluster}_results.json", results_dir / f"{slug}_results.json"]
            for path in candidates:
                if path.exists():
                    paths.append(path)
                    break
            else:
                raise SystemExit(f"No result JSON found for {cluster}")
        return paths
    return sorted(path for path in results_dir.glob("*_results.json") if "_r500_" not in path.name)


def setup_saved_model(result: dict[str, Any]) -> None:
    from sherpa.astro.ui import set_stat, set_method, xsapec, xsphabs, xspowerlaw

    set_stat("wstat")
    set_method("levmar")

    ann = result.get("annulus_fit") or {}
    scale = as_float(result.get("xrb_area_scale_source_over_annulus"), 1.0) or 1.0

    gal_src = xsphabs.gal_src
    gal_src.nH = as_float(result.get("nH_1e22_cm2"), 0.02) or 0.02
    gal_src.nH.freeze()

    lhb_src = xsapec.lhb_src
    lhb_src.kT = as_float(ann.get("lhb_kT"), 0.1) or 0.1
    lhb_src.kT.freeze()
    lhb_src.Abundanc = 1.0
    lhb_src.Abundanc.freeze()
    lhb_src.redshift = 0.0
    lhb_src.redshift.freeze()
    lhb_src.norm = (as_float(ann.get("lhb_norm"), 5.0e-6) or 5.0e-6) * scale
    lhb_src.norm.freeze()

    halo_src = xsapec.halo_src
    halo_src.kT = as_float(ann.get("halo_kT"), 0.25) or 0.25
    halo_src.kT.freeze()
    halo_src.Abundanc = 1.0
    halo_src.Abundanc.freeze()
    halo_src.redshift = 0.0
    halo_src.redshift.freeze()
    halo_src.norm = (as_float(ann.get("halo_norm"), 0.0) or 0.0) * scale
    halo_src.norm.freeze()

    cxb_src = xspowerlaw.cxb_src
    cxb_src.PhoIndex = as_float(ann.get("cxb_phoindex"), 1.4) or 1.4
    cxb_src.PhoIndex.freeze()
    cxb_src.norm = (as_float(ann.get("cxb_norm"), 0.0) or 0.0) * scale
    cxb_src.norm.freeze()

    icm_src = xsapec.icm_src
    icm_src.kT = as_float(result.get("temperature_keV"), 5.0) or 5.0
    icm_src.Abundanc = as_float(result.get("abundance_solar"), 0.3) or 0.3
    icm_src.Abundanc.freeze()
    icm_src.redshift = as_float(result.get("redshift"), 0.0) or 0.0
    icm_src.redshift.freeze()
    icm_src.norm = as_float(result.get("apec_norm"), 1.0e-3) or 1.0e-3


def plot_one(result_path: Path, outdir: Path, suffix: str) -> Path:
    from sherpa.astro.ui import (
        clean,
        get_bkg_plot,
        get_data_plot,
        get_model_plot,
        group_counts,
        ignore_bad,
        load_pha,
        notice_id,
        set_source,
        subtract,
        xsapec,
        xsphabs,
        xspowerlaw,
    )

    plt = configure_matplotlib()
    result = json.loads(result_path.read_text())
    source_spectra = result.get("source_spectra") or []
    if not source_spectra:
        raise SystemExit(f"No source spectra in {result_path}")
    cluster_key = result_path.name.removesuffix("_results.json")
    band = result.get("fit_band_keV") or [0.7, 7.0]

    clean()
    setup_saved_model(result)

    raw_plots = {}
    bkg_plots = {}
    net_plots = {}
    model_plots = {}
    residual_summaries = []

    for idx, pha in enumerate(source_spectra, start=1):
        load_pha(idx, pha)
        try:
            ignore_bad(idx)
        except Exception:
            pass
        notice_id(idx, float(band[0]), float(band[1]))
        group_counts(idx, 1)
        set_source(idx, xsapec.lhb_src + xsphabs.gal_src * (xsapec.halo_src + xspowerlaw.cxb_src + xsapec.icm_src))
        raw_plots[idx] = get_data_plot(idx)
        try:
            bkg_plots[idx] = get_bkg_plot(idx)
        except Exception:
            bkg_plots[idx] = None
        subtract(idx)
        net_plots[idx] = get_data_plot(idx)
        model_plots[idx] = get_model_plot(idx)

    fig, (ax, rax) = plt.subplots(
        2,
        1,
        figsize=(8.4, 6.4),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    positive_values: list[float] = []

    for idx, pha in enumerate(source_spectra, start=1):
        color = colors[(idx - 1) % len(colors)]
        label = Path(pha).name.replace(".pi", "")
        raw = raw_plots[idx]
        bkg = bkg_plots[idx]
        net = net_plots[idx]
        model = model_plots[idx]

        raw_y = np.asarray(raw.y, dtype=float)
        raw_mask = np.isfinite(raw_y) & (raw_y > 0)
        ax.plot(np.asarray(raw.x)[raw_mask], raw_y[raw_mask], color=color, lw=0.8, alpha=0.18)

        if bkg is not None:
            bkg_y = np.asarray(bkg.y, dtype=float)
            bkg_mask = np.isfinite(bkg_y) & (bkg_y > 0)
            ax.plot(np.asarray(bkg.x)[bkg_mask], bkg_y[bkg_mask], color=color, lw=0.8, alpha=0.18, ls=":")

        net_x = np.asarray(net.x, dtype=float)
        net_y = np.asarray(net.y, dtype=float)
        net_yerr = getattr(net, "yerr", None)
        net_mask = np.isfinite(net_x) & np.isfinite(net_y) & (net_y > 0)
        if net_yerr is not None:
            net_yerr = np.asarray(net_yerr, dtype=float)
            plot_yerr = net_yerr[net_mask]
        else:
            plot_yerr = None
        ax.errorbar(
            net_x[net_mask],
            net_y[net_mask],
            yerr=plot_yerr,
            fmt="o",
            ms=3,
            lw=0.8,
            alpha=0.75,
            color=color,
            label=f"{label} net data",
        )
        model_y = np.asarray(model.y, dtype=float)
        model_mask = np.isfinite(model_y) & (model_y > 0)
        ax.plot(np.asarray(model.x)[model_mask], model_y[model_mask], color=color, lw=1.5, label=f"{label} model")
        positive_values.extend(net_y[net_mask].tolist())
        positive_values.extend(model_y[model_mask].tolist())

        n = min(net_y.size, model_y.size)
        residual = net_y[:n] - model_y[:n]
        if net_yerr is not None:
            denom = np.asarray(net_yerr[:n], dtype=float)
            good = np.isfinite(residual) & np.isfinite(denom) & (denom > 0)
            resid_plot = np.full_like(residual, np.nan, dtype=float)
            resid_plot[good] = residual[good] / denom[good]
            rax.set_ylabel(r"$(net-model)/\sigma$")
        else:
            good = np.isfinite(residual)
            resid_plot = residual
            rax.set_ylabel("Net-model")
        residual_summaries.append(
            {
                "dataset_id": idx,
                "spectrum": pha,
                "n_bins": int(np.sum(good)),
                "mean_residual": float(np.nanmean(resid_plot[good])) if np.any(good) else None,
                "rms_residual": float(np.sqrt(np.nanmean(resid_plot[good] ** 2))) if np.any(good) else None,
                "max_abs_residual": float(np.nanmax(np.abs(resid_plot[good]))) if np.any(good) else None,
            }
        )
        rax.axhline(0, color="0.25", ls="--", lw=0.8)
        rax.errorbar(net_x[:n], resid_plot, yerr=None, fmt="o", ms=2.5, lw=0.7, alpha=0.7, color=color)

    ax.set_yscale("log")
    if positive_values:
        ymin = max(min(positive_values) * 0.5, 1.0e-6)
        ymax = max(positive_values) * 1.6
        ax.set_ylim(ymin, ymax)
    ax.set_ylabel(r"Counts s$^{-1}$ keV$^{-1}$")
    rax.set_xlabel("Energy (keV)")
    ax.set_title("Background-aware source fit")
    ax.text(
        0.02,
        0.03,
        "Primary: net source data vs folded model. Faint solid/dotted lines show raw source/background references.",
        transform=ax.transAxes,
        fontsize=7.5,
        bbox={"facecolor": "white", "edgecolor": "0.7", "alpha": 0.85},
    )
    ax.legend(fontsize=5.8, ncol=2)
    ax.grid(alpha=0.2)
    rax.grid(alpha=0.2)

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{cluster_key}{suffix}"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    result["plot_caveat"] = "Background-aware display: net source data are shown against folded source model; raw source/background are reference overlays."
    result["fit_plot_png"] = str(out)
    result["residual_summaries"] = residual_summaries
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return out


def main() -> None:
    args = parse_args()
    for path in load_result_paths(args.results_dir, args.cluster):
        out = plot_one(path, args.figdir, args.suffix)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
