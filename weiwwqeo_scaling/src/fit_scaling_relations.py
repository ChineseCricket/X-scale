#!/usr/bin/env python
"""Fit literature-style X-ray scaling relations with linmix.

The fit uses the common fixed-evolution form:

    log10(Y / E(z)^gamma) = alpha + beta log10(M500c / 3e14 Msun),

with gamma fixed to the literature comparison convention for each observable.
The free parameters are therefore normalization, mass slope, and intrinsic
scatter.  Measurement errors in logM/logY are handled by Kelly (2007) linmix.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

try:
    import linmix
except ImportError as exc:  # pragma: no cover - user-facing dependency check
    raise SystemExit(
        "linmix is required. Install in the CIAO env with:\n"
        "  /opt/miniconda3/envs/ciao-4.18/bin/pip install "
        "git+https://github.com/jmeyers314/linmix.git"
    ) from exc


RELATIONS = {
    "Lx-M500": {
        "y_col": "Lx_bol_1e44_erg_s",
        "y_label": "log10(E(z)^-2 Lx_bol / 1e44 erg s^-1)",
        "default_frac_err": 0.10,
        "fixed_gamma": 2.0,
        "self_similar_beta": 4.0 / 3.0,
        "self_similar_gamma": 2.0,
        "model_label": r"$E(z)^{-2}L_X=A(M_{500c}/3\times10^{14}M_\odot)^\beta$",
        "literature": [
            {
                "paper": "Mantz et al. 2010",
                "quantity": "core-excised Lx-M500 slope",
                "value": 1.33,
                "err": 0.08,
                "note": "wiki/papers/mantz_2010.md; ROSAT 0.1-2.4 keV, core-excised.",
            },
            {
                "paper": "Pratt et al. 2009",
                "quantity": "Lx-M500 context",
                "value": None,
                "err": None,
                "note": "wiki/papers/pratt_2009.md; REXCESS bolometric Lx slopes are steeper than self-similar, mass is Yx-derived.",
            },
        ],
    },
    "Tx-M500": {
        "y_col": "Tx_keV",
        "y_label": "log10(E(z)^(-2/3) Tx / keV)",
        "default_frac_err": None,
        "fixed_gamma": 2.0 / 3.0,
        "self_similar_beta": 2.0 / 3.0,
        "self_similar_gamma": 2.0 / 3.0,
        "model_label": r"$E(z)^{-2/3}T_X=A(M_{500c}/3\times10^{14}M_\odot)^\beta$",
        "literature": [
            {
                "paper": "Mantz et al. 2010",
                "quantity": "Tx-M500 context",
                "value": None,
                "err": None,
                "note": "wiki/papers/mantz_2010.md; slope consistent with or slightly steeper than self-similar, 10-15% scatter.",
            },
            {
                "paper": "Maughan et al. 2012",
                "quantity": "Lx-T context",
                "value": None,
                "err": None,
                "note": "wiki/papers/maughan_2012.md; core-excised relaxed Lx-T is close to self-similar, disturbed systems are steeper.",
            },
        ],
    },
}

QUALITY_STYLES = {
    "good": {"label": "good", "color": "#1f5fd0", "marker": "o"},
    "acceptable": {"label": "acceptable", "color": "#2f9e44", "marker": "s"},
    "high": {"label": "high/low vs ACCEPT", "color": "#f08c00", "marker": "^"},
    "bad": {"label": "bad/failed", "color": "#d6336c", "marker": "X"},
    "unknown": {"label": "unknown", "color": "#868e96", "marker": "D"},
}

SAMPLES = {
    "all": {
        "label": "all fitted clusters",
        "description": "All rows with status=done and positive M500/Y.",
        "exclude_bad": False,
    },
    "exclude_bad": {
        "label": "excluding bad/failed fits",
        "description": "Excludes rows classified as bad: rstat >= 3, ACCEPT ratio < 0.5, ACCEPT ratio > 5, or missing Tx errors.",
        "exclude_bad": True,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--summary",
        default="output/products/spectral/spectral_twostep_summary.csv",
        help="Input Phase 3 spectral summary CSV.",
    )
    parser.add_argument(
        "--outdir",
        default="weiwwqeo_scaling/products",
        help="Directory for JSON/CSV/Markdown fit products.",
    )
    parser.add_argument(
        "--figdir",
        default="weiwwqeo_scaling/figures",
        help="Directory for scaling-relation figures.",
    )
    parser.add_argument(
        "--omega-m",
        type=float,
        default=0.3,
        help="Omega_M for E(z)=sqrt(Omega_M(1+z)^3+Omega_L).",
    )
    parser.add_argument(
        "--mass-frac-err",
        type=float,
        default=0.20,
        help="Assumed fractional 1-sigma WL M500 uncertainty when no table column is present.",
    )
    parser.add_argument(
        "--lx-frac-err",
        type=float,
        default=0.10,
        help="Assumed fractional 1-sigma Lx uncertainty when no table column is present.",
    )
    parser.add_argument("--k", type=int, default=2, help="Number of Gaussian mixture components in linmix.")
    parser.add_argument("--chains", type=int, default=2, help="Number of linmix chains.")
    parser.add_argument("--miniter", type=int, default=1200, help="Minimum linmix MCMC iterations.")
    parser.add_argument("--maxiter", type=int, default=3000, help="Maximum linmix MCMC iterations.")
    parser.add_argument("--seed", type=int, default=20260527)
    return parser.parse_args()


def as_float(row: dict[str, str], key: str) -> float | None:
    val = row.get(key, "")
    if val is None or val == "":
        return None
    try:
        out = float(val)
    except ValueError:
        return None
    if not math.isfinite(out):
        return None
    return out


def ez(redshift: np.ndarray, omega_m: float) -> np.ndarray:
    omega_l = 1.0 - omega_m
    return np.sqrt(omega_m * (1.0 + redshift) ** 3 + omega_l)


def load_done_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if row.get("status") == "done"]


def classify_quality(row: dict[str, str]) -> str:
    rstat = as_float(row, "rstat")
    ratio = as_float(row, "ratio_Tx_accept")
    tx_err_lo = as_float(row, "Tx_err_lo")
    tx_err_hi = as_float(row, "Tx_err_hi")

    if rstat is not None and rstat >= 3.0:
        return "bad"
    if ratio is not None and (ratio < 0.5 or ratio > 5.0):
        return "bad"
    if tx_err_lo is None or tx_err_hi is None:
        return "bad"
    if ratio is None:
        return "unknown"
    if 0.8 <= ratio <= 1.2:
        return "good"
    if 0.5 <= ratio <= 1.5:
        return "acceptable"
    return "high"


def quality_counts(quality: list[str]) -> dict[str, int]:
    return {key: quality.count(key) for key in QUALITY_STYLES if quality.count(key)}


def write_quality_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["cluster_key", "quality", "excluded_from_exclude_bad", "Tx_keV", "rstat", "qval", "ratio_Tx_accept", "qa_flags"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            quality = classify_quality(row)
            writer.writerow(
                {
                    "cluster_key": row.get("cluster_key", ""),
                    "quality": quality,
                    "excluded_from_exclude_bad": quality == "bad",
                    "Tx_keV": row.get("Tx_keV", ""),
                    "rstat": row.get("rstat", ""),
                    "qval": row.get("qval", ""),
                    "ratio_Tx_accept": row.get("ratio_Tx_accept", ""),
                    "qa_flags": row.get("qa_flags", ""),
                }
            )


def build_arrays(
    rows: list[dict[str, str]],
    relation: str,
    omega_m: float,
    mass_frac_err: float,
    lx_frac_err: float,
    sample_key: str,
) -> dict[str, Any]:
    spec = RELATIONS[relation]
    used: list[dict[str, str]] = []
    for row in rows:
        quality = classify_quality(row)
        if SAMPLES[sample_key]["exclude_bad"] and quality == "bad":
            continue
        if (
            as_float(row, "M500_1e14_msun")
            and as_float(row, "z") is not None
            and as_float(row, spec["y_col"])
            and as_float(row, spec["y_col"]) > 0
        ):
            used.append(row)

    mass = np.array([as_float(row, "M500_1e14_msun") for row in used], dtype=float)
    redshift = np.array([as_float(row, "z") for row in used], dtype=float)
    y_linear = np.array([as_float(row, spec["y_col"]) for row in used], dtype=float)

    x = np.log10(mass / 3.0)
    e_term = np.log10(ez(redshift, omega_m))
    y = np.log10(y_linear)
    xsig = np.full_like(x, mass_frac_err / math.log(10.0))

    if relation == "Tx-M500":
        ysig_linear = []
        for row in used:
            tx = as_float(row, "Tx_keV")
            lo = as_float(row, "Tx_err_lo")
            hi = as_float(row, "Tx_err_hi")
            if tx and lo and hi:
                ysig_linear.append(0.5 * (lo + hi) / tx / math.log(10.0))
            else:
                ysig_linear.append(0.10 / math.log(10.0))
        ysig = np.array(ysig_linear, dtype=float)
        y_error_note = "Tx errors from Tx_err_lo/Tx_err_hi, symmetrized in log10."
    else:
        ysig = np.full_like(y, lx_frac_err / math.log(10.0))
        y_error_note = (
            f"Lx errors are not present in the summary table; assumed {lx_frac_err:.0%} fractional 1-sigma."
        )

    return {
        "clusters": [row["cluster_key"] for row in used],
        "quality": [classify_quality(row) for row in used],
        "sample_key": sample_key,
        "sample_label": SAMPLES[sample_key]["label"],
        "x": x,
        "xsig": xsig,
        "e_term": e_term,
        "y": y,
        "ysig": ysig,
        "mass": mass,
        "redshift": redshift,
        "y_linear": y_linear,
        "notes": [
            f"M500 errors are not present in the summary table; assumed {mass_frac_err:.0%} fractional 1-sigma.",
            y_error_note,
            SAMPLES[sample_key]["description"],
        ],
    }


def summarize(samples: np.ndarray) -> dict[str, float]:
    pct = np.percentile(samples, [16, 50, 84])
    return {
        "median": float(pct[1]),
        "err_lo": float(pct[1] - pct[0]),
        "err_hi": float(pct[2] - pct[1]),
        "p16": float(pct[0]),
        "p84": float(pct[2]),
    }


def run_linmix(
    x: np.ndarray,
    y: np.ndarray,
    xsig: np.ndarray,
    ysig: np.ndarray,
    k: int,
    chains: int,
    miniter: int,
    maxiter: int,
    seed: int,
) -> np.recarray:
    lm = linmix.LinMix(
        x,
        y,
        xsig=xsig,
        ysig=ysig,
        K=k,
        nchains=chains,
        parallelize=False,
        seed=seed,
    )
    lm.run_mcmc(miniter=miniter, maxiter=maxiter, silent=True)
    return lm.chain


def fit_relation(name: str, arrays: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    spec = RELATIONS[name]
    gamma = float(spec["fixed_gamma"])
    ycorr = arrays["y"] - gamma * arrays["e_term"]
    chain = run_linmix(
        arrays["x"],
        ycorr,
        arrays["xsig"],
        arrays["ysig"],
        args.k,
        args.chains,
        args.miniter,
        args.maxiter,
        args.seed + (0 if name == "Lx-M500" else 50000),
    )

    alpha_samples = chain["alpha"]
    beta_samples = chain["beta"]
    scatter_samples = np.sqrt(np.maximum(chain["sigsqr"], 0.0))
    gamma_summary = {"median": gamma, "err_lo": 0.0, "err_hi": 0.0, "p16": gamma, "p84": gamma}

    residual = ycorr - (np.median(alpha_samples) + np.median(beta_samples) * arrays["x"])
    rms = float(np.sqrt(np.mean(residual**2)))

    return {
        "sample": arrays["sample_key"],
        "sample_label": arrays["sample_label"],
        "relation": name,
        "n_clusters": len(arrays["clusters"]),
        "clusters": arrays["clusters"],
        "quality_counts": quality_counts(arrays["quality"]),
        "x_definition": "log10(M500c / 3e14 Msun)",
        "e_definition": f"log10(E(z)); Omega_M={args.omega_m:.3f}, Omega_L={1.0 - args.omega_m:.3f}",
        "y_definition": spec["y_label"],
        "model": "log10(Y / E(z)^gamma_fixed) = alpha + beta*log10(M500c / 3e14 Msun)",
        "model_label": spec["model_label"],
        "alpha": summarize(alpha_samples),
        "beta": summarize(beta_samples),
        "gamma": gamma_summary,
        "intrinsic_scatter_dex": summarize(scatter_samples),
        "observed_rms_dex": rms,
        "n_chain": int(len(chain)),
        "self_similar": {
            "beta": spec["self_similar_beta"],
            "gamma": spec["self_similar_gamma"],
        },
        "literature": spec["literature"],
        "assumptions": arrays["notes"]
        + [
            f"Evolution exponent gamma is fixed to {gamma:.6g} for literature-style comparison.",
            "All logarithms are base 10.",
            "Rows with status != done or missing positive Y/M500 were excluded.",
        ],
    }


def write_csv(path: Path, results: list[dict[str, Any]]) -> None:
    fields = [
        "sample",
        "sample_label",
        "relation",
        "n_clusters",
        "quality_counts",
        "alpha",
        "alpha_err_lo",
        "alpha_err_hi",
        "beta",
        "beta_err_lo",
        "beta_err_hi",
        "gamma",
        "gamma_err_lo",
        "gamma_err_hi",
        "intrinsic_scatter_dex",
        "scatter_err_lo",
        "scatter_err_hi",
        "observed_rms_dex",
        "model",
        "self_similar_beta",
        "self_similar_gamma",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "sample": result["sample"],
                    "sample_label": result["sample_label"],
                    "relation": result["relation"],
                    "n_clusters": result["n_clusters"],
                    "quality_counts": json.dumps(result["quality_counts"], sort_keys=True),
                    "alpha": result["alpha"]["median"],
                    "alpha_err_lo": result["alpha"]["err_lo"],
                    "alpha_err_hi": result["alpha"]["err_hi"],
                    "beta": result["beta"]["median"],
                    "beta_err_lo": result["beta"]["err_lo"],
                    "beta_err_hi": result["beta"]["err_hi"],
                    "gamma": result["gamma"]["median"],
                    "gamma_err_lo": result["gamma"]["err_lo"],
                    "gamma_err_hi": result["gamma"]["err_hi"],
                    "intrinsic_scatter_dex": result["intrinsic_scatter_dex"]["median"],
                    "scatter_err_lo": result["intrinsic_scatter_dex"]["err_lo"],
                    "scatter_err_hi": result["intrinsic_scatter_dex"]["err_hi"],
                    "observed_rms_dex": result["observed_rms_dex"],
                    "model": result["model"],
                    "self_similar_beta": result["self_similar"]["beta"],
                    "self_similar_gamma": result["self_similar"]["gamma"],
                }
            )


def fmt_pm(summary: dict[str, float]) -> str:
    return f"{summary['median']:.3f} -{summary['err_lo']:.3f}/+{summary['err_hi']:.3f}"


def write_markdown(
    path: Path,
    results: list[dict[str, Any]],
    args: argparse.Namespace,
    figure_paths: list[Path] | None = None,
) -> None:
    lines = [
        "# Preliminary Scaling Relation Fits",
        "",
        f"Input: `{args.summary}`",
        "",
        "Model:",
        "",
        "`log10(Y / E(z)^gamma_fixed) = alpha + beta log10(M500c / 3e14 Msun)`",
        "",
        "M500c is the weak-lensing mass, independent of the X-ray observables. The redshift exponent is fixed to the literature comparison value rather than fit freely.",
        "",
        "- Lx-M500c: `E(z)^-2 Lx_bol = A (M500c / 3e14 Msun)^beta`",
        "- Tx-M500c: `E(z)^(-2/3) Tx = A (M500c / 3e14 Msun)^beta`",
        "",
        "## Results",
        "",
        "| Sample | Relation | N | quality counts | alpha | beta | fixed gamma | intrinsic scatter (dex) | observed RMS (dex) | self-similar beta/gamma |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            "| {sample} | {relation} | {n} | {counts} | {alpha} | {beta} | {gamma} | {scatter} | {rms:.3f} | {ssb:.3f}/{ssg:.3f} |".format(
                sample=result["sample"],
                relation=result["relation"],
                n=result["n_clusters"],
                counts=", ".join(f"{key}:{value}" for key, value in result["quality_counts"].items()),
                alpha=fmt_pm(result["alpha"]),
                beta=fmt_pm(result["beta"]),
                gamma=fmt_pm(result["gamma"]),
                scatter=fmt_pm(result["intrinsic_scatter_dex"]),
                rms=result["observed_rms_dex"],
                ssb=result["self_similar"]["beta"],
                ssg=result["self_similar"]["gamma"],
            )
        )

    if figure_paths:
        lines.extend(["", "## Figures", ""])
        for figure_path in figure_paths:
            lines.append(f"- `{figure_path}`")

    lines.extend(["", "## Literature Context", ""])
    for result in results:
        lines.append(f"### {result['relation']}")
        for item in result["literature"]:
            if item["value"] is None:
                lines.append(f"- {item['paper']}: {item['note']}")
            else:
                lines.append(
                    f"- {item['paper']}: {item['quantity']} = {item['value']:.2f} +/- {item['err']:.2f}. {item['note']}"
                )
        lines.append("")

    lines.extend(["## Assumptions", ""])
    seen = set()
    for result in results:
        for assumption in result["assumptions"]:
            if assumption not in seen:
                lines.append(f"- {assumption}")
                seen.add(assumption)
    lines.append("")

    path.write_text("\n".join(lines))


def linear_logerr(value: np.ndarray, logerr: np.ndarray) -> np.ndarray:
    return value * math.log(10.0) * logerr


def configure_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/matplotlib-codex")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "serif",
            "mathtext.fontset": "dejavuserif",
            "axes.linewidth": 1.0,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "figure.dpi": 140,
            "savefig.dpi": 220,
        }
    )
    return plt


def fit_curve_y(result: dict[str, Any], mass_1e14: np.ndarray, gamma_correction: float) -> np.ndarray:
    alpha = result["alpha"]["median"]
    beta = result["beta"]["median"]
    x = np.log10(mass_1e14 / 3.0)
    return 10.0 ** (alpha + beta * x)


def add_scatter_band(ax: Any, x: np.ndarray, y: np.ndarray, scatter_dex: float, color: str) -> None:
    factor = 10.0**scatter_dex
    ax.fill_between(x, y / factor, y * factor, color=color, alpha=0.16, linewidth=0)


def plot_quality_points(
    ax: Any,
    x: np.ndarray,
    y: np.ndarray,
    xerr: np.ndarray,
    yerr: np.ndarray,
    quality: list[str],
    default_color: str,
) -> None:
    quality_arr = np.array(quality)
    for key, style in QUALITY_STYLES.items():
        mask = quality_arr == key
        if not np.any(mask):
            continue
        color = style["color"] if key != "unknown" else default_color
        ax.errorbar(
            x[mask],
            y[mask],
            xerr=xerr[mask],
            yerr=yerr[mask],
            fmt=style["marker"],
            ms=5.4,
            color=color,
            ecolor=color,
            elinewidth=1.0,
            capsize=2,
            linestyle="none",
            label=f"{style['label']} ({int(np.sum(mask))})",
        )


def write_figures(
    figdir: Path,
    results: list[dict[str, Any]],
    arrays_by_relation: dict[str, dict[str, Any]],
    args: argparse.Namespace,
    sample_key: str,
) -> list[Path]:
    plt = configure_matplotlib()
    figdir.mkdir(parents=True, exist_ok=True)
    result_by_name = {item["relation"]: item for item in results}
    paths: list[Path] = []

    lx = arrays_by_relation["Lx-M500"]
    lx_result = result_by_name["Lx-M500"]
    lx_plot_evolution = lx_result["gamma"]["median"]
    lx_e = ez(lx["redshift"], args.omega_m)
    mass_grid = np.logspace(
        math.log10(np.min(lx["mass"]) * 0.75),
        math.log10(np.max(lx["mass"]) * 1.25),
        200,
    )
    lx_line = fit_curve_y(lx_result, mass_grid, lx_plot_evolution)

    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    plot_quality_points(
        ax,
        lx["mass"],
        lx["y_linear"] / lx_e**lx_plot_evolution,
        linear_logerr(lx["mass"], lx["xsig"]),
        linear_logerr(lx["y_linear"] / lx_e**lx_plot_evolution, lx["ysig"]),
        lx["quality"],
        "#1f5fd0",
    )
    add_scatter_band(ax, mass_grid, lx_line, lx_result["intrinsic_scatter_dex"]["median"], "#1f5fd0")
    ax.plot(mass_grid, lx_line, color="#1f5fd0", lw=2.0, label=lx_result["model_label"])

    mantz_beta = 1.33
    mantz_norm = 10.0 ** lx_result["alpha"]["median"]
    mantz_line = mantz_norm * (mass_grid / 3.0) ** mantz_beta
    ax.plot(mass_grid, mantz_line, color="0.25", ls="--", lw=1.4, label=r"Mantz+10: $\beta=1.33$")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$M_{500c,\rm WL}\ (10^{14}\ M_\odot)$")
    ax.set_ylabel(r"$E(z)^{-2}\ L_{\rm X,bol}\ (10^{44}\ {\rm erg\ s^{-1}})$")
    ax.set_title(rf"$L_X-M_{{500c}}$ ({SAMPLES[sample_key]['label']})")
    ax.legend(frameon=False, fontsize=7.6)
    ax.text(
        0.04,
        0.04,
        rf"$\beta={lx_result['beta']['median']:.2f}^{{+{lx_result['beta']['err_hi']:.2f}}}_{{-{lx_result['beta']['err_lo']:.2f}}}$"
        "\n"
        rf"$\sigma_{{\rm int}}={lx_result['intrinsic_scatter_dex']['median']:.2f}$ dex",
        transform=ax.transAxes,
        fontsize=10,
    )
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        out = figdir / f"lx_m500_linmix_{sample_key}.{suffix}"
        fig.savefig(out)
        paths.append(out)
    plt.close(fig)

    tx = arrays_by_relation["Tx-M500"]
    tx_result = result_by_name["Tx-M500"]
    tx_gamma = tx_result["gamma"]["median"]
    tx_e = ez(tx["redshift"], args.omega_m)
    mass_grid = np.logspace(
        math.log10(np.min(tx["mass"]) * 0.75),
        math.log10(np.max(tx["mass"]) * 1.25),
        200,
    )
    tx_line = fit_curve_y(tx_result, mass_grid, tx_gamma)

    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    plot_quality_points(
        ax,
        tx["mass"],
        tx["y_linear"] / tx_e**tx_gamma,
        linear_logerr(tx["mass"], tx["xsig"]),
        linear_logerr(tx["y_linear"] / tx_e**tx_gamma, tx["ysig"]),
        tx["quality"],
        "#c22f2f",
    )
    add_scatter_band(ax, mass_grid, tx_line, tx_result["intrinsic_scatter_dex"]["median"], "#c22f2f")
    ax.plot(mass_grid, tx_line, color="#c22f2f", lw=2.0, label=tx_result["model_label"])

    ss_norm = 10.0 ** tx_result["alpha"]["median"]
    ss_line = ss_norm * (mass_grid / 3.0) ** (2.0 / 3.0)
    ax.plot(mass_grid, ss_line, color="0.25", ls="--", lw=1.4, label="self-similar slope 2/3")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$M_{500c,\rm WL}\ (10^{14}\ M_\odot)$")
    ax.set_ylabel(r"$E(z)^{-2/3}\ T_X\ ({\rm keV})$")
    ax.set_title(rf"$T_X-M_{{500c}}$ ({SAMPLES[sample_key]['label']})")
    ax.legend(frameon=False, fontsize=7.6)
    ax.text(
        0.04,
        0.04,
        rf"$\beta={tx_result['beta']['median']:.2f}^{{+{tx_result['beta']['err_hi']:.2f}}}_{{-{tx_result['beta']['err_lo']:.2f}}}$"
        "\n"
        rf"$\sigma_{{\rm int}}={tx_result['intrinsic_scatter_dex']['median']:.2f}$ dex",
        transform=ax.transAxes,
        fontsize=10,
    )
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        out = figdir / f"tx_m500_linmix_{sample_key}.{suffix}"
        fig.savefig(out)
        paths.append(out)
    plt.close(fig)

    # Literature-style M-T view: self-similar expectation is E(z) M500 ∝ T_X^(3/2).
    tx_grid = np.logspace(math.log10(np.min(tx["y_linear"]) * 0.8), math.log10(np.max(tx["y_linear"]) * 1.2), 200)
    beta = tx_result["beta"]["median"]
    alpha = tx_result["alpha"]["median"]
    gamma = tx_result["gamma"]["median"]
    mass_from_tx = 3.0 * 10.0 ** ((np.log10(tx_grid) - alpha) / beta)
    ss_mass_from_tx = 3.0 * 10.0 ** ((np.log10(tx_grid) - alpha) / (2.0 / 3.0))

    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    plot_quality_points(
        ax,
        tx["y_linear"],
        tx["mass"] * tx_e,
        linear_logerr(tx["y_linear"], tx["ysig"]),
        linear_logerr(tx["mass"] * tx_e, tx["xsig"]),
        tx["quality"],
        "#2459ff",
    )
    ax.plot(
        tx_grid,
        mass_from_tx,
        color="#2459ff",
        lw=2.0,
        label=r"inverted fit: $E(z)^{-2/3}T_X=A(M_{500c}/3\times10^{14}M_\odot)^\beta$",
    )
    ax.plot(tx_grid, ss_mass_from_tx, color="0.25", ls="-.", lw=1.4, label=r"$E(z)M_{500}\propto T_X^{3/2}$")
    ax.fill_between(
        tx_grid,
        mass_from_tx / 10.0 ** (tx_result["intrinsic_scatter_dex"]["median"] / max(beta, 1.0e-3)),
        mass_from_tx * 10.0 ** (tx_result["intrinsic_scatter_dex"]["median"] / max(beta, 1.0e-3)),
        color="#2459ff",
        alpha=0.14,
        linewidth=0,
        label="intrinsic scatter",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$T_X\ ({\rm keV})$")
    ax.set_ylabel(r"$E(z)\ M_{500c,\rm WL}\ (10^{14}\ M_\odot)$")
    ax.set_title(rf"Literature-style $M_{{500c}}-T_X$ ({SAMPLES[sample_key]['label']})")
    ax.legend(frameon=False, fontsize=7.6, loc="upper left")
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        out = figdir / f"m500_tx_literature_style_{sample_key}.{suffix}"
        fig.savefig(out)
        paths.append(out)
    plt.close(fig)

    return paths


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_done_rows(summary_path)
    all_results: list[dict[str, Any]] = []
    all_figure_paths: list[Path] = []
    quality_csv = outdir / "scaling_quality_classification.csv"
    write_quality_csv(quality_csv, rows)
    print(f"Wrote {quality_csv}")

    for sample_key in SAMPLES:
        results = []
        arrays_by_relation = {}
        for relation in ("Lx-M500", "Tx-M500"):
            arrays = build_arrays(rows, relation, args.omega_m, args.mass_frac_err, args.lx_frac_err, sample_key)
            if len(arrays["clusters"]) < 5:
                raise SystemExit(f"Not enough clusters for {sample_key}/{relation}: {len(arrays['clusters'])}")
            arrays_by_relation[relation] = arrays
            results.append(fit_relation(relation, arrays, args))

        json_path = outdir / f"scaling_linmix_fixed_evolution_{sample_key}_results.json"
        csv_path = outdir / f"scaling_linmix_fixed_evolution_{sample_key}_summary.csv"
        md_path = outdir / f"scaling_linmix_fixed_evolution_{sample_key}_report.md"
        figure_paths = write_figures(Path(args.figdir), results, arrays_by_relation, args, sample_key)

        json_path.write_text(json.dumps(results, indent=2))
        write_csv(csv_path, results)
        write_markdown(md_path, results, args, figure_paths)

        all_results.extend(results)
        all_figure_paths.extend(figure_paths)

        print(f"Wrote {json_path}")
        print(f"Wrote {csv_path}")
        print(f"Wrote {md_path}")
        for figure_path in figure_paths:
            print(f"Wrote {figure_path}")
        for result in results:
            print(
                "{sample}/{relation}: alpha={alpha}, beta={beta}, gamma={gamma}, scatter={scatter} dex; quality={quality}".format(
                    sample=result["sample"],
                    relation=result["relation"],
                    alpha=fmt_pm(result["alpha"]),
                    beta=fmt_pm(result["beta"]),
                    gamma=fmt_pm(result["gamma"]),
                    scatter=fmt_pm(result["intrinsic_scatter_dex"]),
                    quality=result["quality_counts"],
                )
            )

    comparison_json = outdir / "scaling_linmix_fixed_evolution_comparison_results.json"
    comparison_csv = outdir / "scaling_linmix_fixed_evolution_comparison_summary.csv"
    comparison_md = outdir / "scaling_linmix_fixed_evolution_comparison_report.md"
    comparison_json.write_text(json.dumps(all_results, indent=2))
    write_csv(comparison_csv, all_results)
    write_markdown(comparison_md, all_results, args, all_figure_paths)
    print(f"Wrote {comparison_json}")
    print(f"Wrote {comparison_csv}")
    print(f"Wrote {comparison_md}")


if __name__ == "__main__":
    main()
