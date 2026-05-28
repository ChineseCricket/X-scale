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


def spectrum_label(path: str) -> str:
    stem = Path(path).name.replace(".pi", "")
    parts = stem.split("_")
    obs = next((part.replace("obs", "ObsID ") for part in parts if part.startswith("obs")), None)
    return obs or stem


def snapshot_plot(plot: Any) -> dict[str, np.ndarray | None]:
    yerr = getattr(plot, "yerr", None)
    return {
        "x": np.asarray(plot.x, dtype=float).copy(),
        "y": np.asarray(plot.y, dtype=float).copy(),
        "yerr": None if yerr is None else np.asarray(yerr, dtype=float).copy(),
    }


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
    component_plots = {}
    residual_summaries = []
    plot_caveat = (
        "Three-panel background-aware display: raw source and blank-sky/background are shown separately; "
        "net source data are compared with folded total and component source-region models."
    )

    for idx, pha in enumerate(source_spectra, start=1):
        load_pha(idx, pha)
        try:
            ignore_bad(idx)
        except Exception:
            pass
        notice_id(idx, float(band[0]), float(band[1]))
        group_counts(idx, 1)
        total_model = xsapec.lhb_src + xsphabs.gal_src * (xsapec.halo_src + xspowerlaw.cxb_src + xsapec.icm_src)
        component_models = {
            "ICM": xsphabs.gal_src * xsapec.icm_src,
            "LHB": xsapec.lhb_src,
            "Halo": xsphabs.gal_src * xsapec.halo_src,
            "CXB": xsphabs.gal_src * xspowerlaw.cxb_src,
        }
        set_source(idx, total_model)
        raw_plots[idx] = snapshot_plot(get_data_plot(idx))
        try:
            bkg_plots[idx] = snapshot_plot(get_bkg_plot(idx))
        except Exception:
            bkg_plots[idx] = None
        subtract(idx)
        net_plots[idx] = snapshot_plot(get_data_plot(idx))
        model_plots[idx] = snapshot_plot(get_model_plot(idx))
        component_plots[idx] = {}
        for name, component_model in component_models.items():
            try:
                set_source(idx, component_model)
                component_plots[idx][name] = snapshot_plot(get_model_plot(idx))
            except Exception:
                component_plots[idx][name] = None
        set_source(idx, total_model)

    fig, (raw_ax, fit_ax, rax) = plt.subplots(
        3,
        1,
        figsize=(9.2, 8.4),
        sharex=True,
        gridspec_kw={"height_ratios": [1.35, 3, 1], "hspace": 0.06},
    )
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    component_styles = {
        "ICM": {"ls": "--", "lw": 1.25, "alpha": 0.78},
        "LHB": {"ls": ":", "lw": 1.15, "alpha": 0.78},
        "Halo": {"ls": "-.", "lw": 1.15, "alpha": 0.78},
        "CXB": {"ls": (0, (3, 1, 1, 1)), "lw": 1.15, "alpha": 0.78},
    }
    raw_positive_values: list[float] = []
    fit_positive_values: list[float] = []

    for idx, pha in enumerate(source_spectra, start=1):
        color = colors[(idx - 1) % len(colors)]
        label = spectrum_label(pha)
        raw = raw_plots[idx]
        bkg = bkg_plots[idx]

        raw_y = raw["y"]
        raw_x = raw["x"]
        raw_yerr = raw["yerr"]
        raw_mask = np.isfinite(raw_x) & np.isfinite(raw_y) & (raw_y > 0)
        if raw_yerr is not None:
            raw_plot_yerr = raw_yerr[raw_mask]
        else:
            raw_plot_yerr = None
        raw_ax.errorbar(
            raw_x[raw_mask],
            raw_y[raw_mask],
            yerr=raw_plot_yerr,
            fmt="o",
            ms=2.2,
            lw=0.65,
            alpha=0.72,
            color=color,
            label=f"{label} raw src",
        )
        raw_positive_values.extend(raw_y[raw_mask].tolist())

        if bkg is not None:
            bkg_y = bkg["y"]
            bkg_x = bkg["x"]
            bkg_mask = np.isfinite(bkg_x) & np.isfinite(bkg_y) & (bkg_y > 0)
            raw_ax.plot(
                bkg_x[bkg_mask],
                bkg_y[bkg_mask],
                color=color,
                lw=1.15,
                alpha=0.85,
                ls="--",
                label=f"{label} blank-sky",
            )
            raw_positive_values.extend(bkg_y[bkg_mask].tolist())

    for idx, pha in enumerate(source_spectra, start=1):
        color = colors[(idx - 1) % len(colors)]
        label = spectrum_label(pha)
        net = net_plots[idx]
        model = model_plots[idx]

        net_x = net["x"]
        net_y = net["y"]
        net_yerr = net["yerr"]
        net_mask = np.isfinite(net_x) & np.isfinite(net_y) & (net_y > 0)
        if net_yerr is not None:
            plot_yerr = net_yerr[net_mask]
        else:
            plot_yerr = None
        fit_ax.errorbar(
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
        fit_positive_values.extend(net_y[net_mask].tolist())

        model_y = model["y"]
        model_x = model["x"]
        model_mask = np.isfinite(model_x) & np.isfinite(model_y) & (model_y > 0)
        fit_ax.plot(model_x[model_mask], model_y[model_mask], color=color, lw=1.8, label=f"{label} total model")
        fit_positive_values.extend(model_y[model_mask].tolist())

        for component_name, component_plot in component_plots[idx].items():
            if component_plot is None:
                continue
            comp_y = component_plot["y"]
            comp_x = component_plot["x"]
            comp_mask = np.isfinite(comp_x) & np.isfinite(comp_y) & (comp_y > 0)
            comp_label = f"{component_name} component" if idx == 1 else "_nolegend_"
            fit_ax.plot(
                comp_x[comp_mask],
                comp_y[comp_mask],
                color=color,
                label=comp_label,
                **component_styles[component_name],
            )

        n = min(net_y.size, model_y.size)
        residual = net_y[:n] - model_y[:n]
        if net_yerr is not None:
            denom = net_yerr[:n]
            good = np.isfinite(residual) & np.isfinite(denom) & (denom > 0)
            resid_plot = np.full_like(residual, np.nan, dtype=float)
            resid_plot[good] = residual[good] / denom[good]
            rax.set_ylabel(r"$(net-total)/\sigma$")
        else:
            good = np.isfinite(residual)
            resid_plot = residual
            rax.set_ylabel("Net-total")
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

    raw_ax.set_yscale("log")
    fit_ax.set_yscale("log")
    if raw_positive_values:
        raw_ax.set_ylim(max(min(raw_positive_values) * 0.55, 1.0e-6), max(raw_positive_values) * 1.5)
    if fit_positive_values:
        fit_ax.set_ylim(max(min(fit_positive_values) * 0.55, 1.0e-6), max(fit_positive_values) * 1.6)
    raw_ax.set_ylabel(r"Raw counts s$^{-1}$ keV$^{-1}$")
    fit_ax.set_ylabel(r"Net counts s$^{-1}$ keV$^{-1}$")
    rax.set_xlabel("Energy (keV)")
    raw_ax.set_title("Background-aware source fit diagnostics")
    fit_ax.text(
        0.02,
        0.03,
        "Middle panel: net source data vs folded total model; dashed curves are folded source-region components.",
        transform=fit_ax.transAxes,
        fontsize=7.5,
        bbox={"facecolor": "white", "edgecolor": "0.7", "alpha": 0.85},
    )
    raw_ax.legend(fontsize=5.8, ncol=2)
    fit_ax.legend(fontsize=5.6, ncol=3)
    for axis in (raw_ax, fit_ax, rax):
        axis.grid(alpha=0.2)

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{cluster_key}{suffix}"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    result["plot_caveat"] = plot_caveat
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
