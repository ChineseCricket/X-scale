#!/usr/bin/env python3
"""Build the canonical full-R500 spectral table for Phase 4 scaling.

This table supersedes the older ``spectral_twostep_summary.csv`` as the
scaling input.  Static cluster metadata come from ``configs/cluster_table.csv``;
latest spectral quantities come from ``output/products/spectral/*_results.json``;
quality and exclusion decisions come from ``memory/pipeline_status.csv``.
"""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any


PIPELINE_STATUS = Path("memory/pipeline_status.csv")
CLUSTER_TABLE = Path("configs/cluster_table.csv")
ACCEPT_REFERENCE = Path("configs/accept_reference.csv")
LEGACY_SUMMARY = Path("output/products/spectral/spectral_twostep_summary.csv")
RESULTS_DIR = Path("output/products/spectral")
OUTPUT_CSV = Path("output/products/spectral/spectral_summary.csv")

FIXED_EXCLUDE = {
    "Abell_0697",
    "Abell_0750",
    "MS2137-2353",
    "RXJ1347.5-1145",
    "ZwCl_0857.9+2107",
}

FIELDNAMES = [
    "cluster_key",
    "config_key",
    "cluster_name",
    "z",
    "nH_1e22",
    "M500_1e14_msun",
    "R500_arcsec",
    "R500_Mpc",
    "Tx_keV",
    "Tx_err_lo",
    "Tx_err_hi",
    "abundance_solar",
    "apec_norm",
    "Lx_bol_1e44_erg_s",
    "Lx_soft_1e44_erg_s",
    "flux_bol_1e12_erg_s_cm2",
    "rstat",
    "qval",
    "dof",
    "n_src_spec",
    "n_ann_spec",
    "R_EM",
    "annulus_rstat",
    "accept_Tx_keV",
    "accept_Lx_1e44_erg_s",
    "ratio_Tx_accept",
    "method",
    "xrb_policy",
    "abundance_policy",
    "fit_band",
    "qa_flags",
    "quality",
    "exclude_from_main_scaling",
    "exclude_reason",
    "spectral_status",
    "status",
    "pipeline_notes",
    "result_json",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def read_pipeline_status(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = path.read_text().splitlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        cluster_key, repro, pipeline, spectral, notes = (line.split(",", 4) + [""])[:5]
        rows.append({
            "cluster_key": cluster_key,
            "repro": repro,
            "pipeline": pipeline,
            "spectral": spectral,
            "notes": notes,
        })
    return rows


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fmt(value: Any, digits: int | None = None) -> str:
    number = as_float(value)
    if number is None:
        return "" if value is None else str(value)
    if digits is None:
        return f"{number:.12g}"
    return f"{number:.{digits}f}"


def slug_key(key: str) -> str:
    return re.sub(r"[.\-+]", "_", key)


def key_forms(key: str) -> list[str]:
    forms = [key, slug_key(key)]
    if "_" in key:
        m = re.match(r"^(.+?)_(\d)_(\d{4})$", key)
        if m:
            forms.extend([
                f"{m.group(1)}.{m.group(2)}-{m.group(3)}",
                f"{m.group(1)}.{m.group(2)}+{m.group(3)}",
            ])
    out: list[str] = []
    for item in forms:
        if item not in out:
            out.append(item)
    return out


def index_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get("cluster_key", "")
        for form in key_forms(key):
            out.setdefault(form, row)
    return out


def find_result_json(cluster_key: str) -> Path | None:
    for form in key_forms(cluster_key):
        path = RESULTS_DIR / f"{slug_key(form)}_results.json"
        if path.exists():
            return path
    return None


def load_json(path: Path | None) -> dict[str, Any]:
    if not path:
        return {}
    with path.open() as handle:
        return json.load(handle)


def quality_for(row: dict[str, str], spectral_status: str, ratio: float | None, rstat: float | None) -> str:
    if spectral_status == "bad":
        return "bad"
    if rstat is not None and rstat >= 3.0:
        return "bad"
    if ratio is None:
        return "unknown"
    if ratio < 0.5 or ratio > 5.0:
        return "bad"
    if 0.8 <= ratio <= 1.2:
        return "good"
    if 0.5 <= ratio <= 1.5:
        return "acceptable"
    return "high"


def main() -> None:
    pipeline = read_pipeline_status(PIPELINE_STATUS)
    configs = index_rows(read_csv(CLUSTER_TABLE))
    accept = index_rows(read_csv(ACCEPT_REFERENCE))
    legacy = index_rows(read_csv(LEGACY_SUMMARY)) if LEGACY_SUMMARY.exists() else {}

    rows: list[dict[str, str]] = []
    for pipe in pipeline:
        key = pipe["cluster_key"]
        cfg = configs.get(key) or configs.get(slug_key(key), {})
        old = legacy.get(key) or legacy.get(slug_key(key), {})
        acc = accept.get(key) or accept.get(slug_key(key), {})
        result_path = find_result_json(key)
        result = load_json(result_path)

        z = as_float(cfg.get("redshift")) or as_float(old.get("z"))
        m500_msun = as_float(cfg.get("m500_physical_msun_h70"))
        m500_1e14 = (m500_msun / 1e14) if m500_msun else as_float(old.get("M500_1e14_msun"))

        tx = as_float(result.get("temperature_keV")) or as_float(old.get("Tx_keV"))
        tx_lo = (
            as_float(result.get("temperature_err_lo_keV"))
            or as_float(result.get("confidence_intervals", {}).get("icm_src.kT", {}).get("lower_delta_1sigma"))
            or as_float(old.get("Tx_err_lo"))
        )
        tx_hi = (
            as_float(result.get("temperature_err_hi_keV"))
            or as_float(result.get("confidence_intervals", {}).get("icm_src.kT", {}).get("upper_delta_1sigma"))
            or as_float(old.get("Tx_err_hi"))
        )
        accept_tx = as_float(acc.get("accept_tx_kev")) or as_float(old.get("accept_Tx_keV"))
        ratio = (tx / accept_tx) if tx and accept_tx else None

        annulus_fit = result.get("annulus_fit") or {}
        source_spectra = result.get("source_spectra") or []
        annulus_spectra = result.get("annulus_spectra") or []
        fit_band = result.get("fit_band_keV") or old.get("fit_band", "")
        if isinstance(fit_band, list) and len(fit_band) == 2:
            fit_band = f"{fit_band[0]:g}-{fit_band[1]:g}"

        spectral_status = pipe.get("spectral", "")
        quality = quality_for(
            old,
            spectral_status,
            ratio,
            as_float(result.get("rstat")) or as_float(old.get("rstat")),
        )
        exclude = key in FIXED_EXCLUDE or quality == "bad"
        exclude_reason = pipe.get("notes", "") if exclude else ""

        rows.append({
            "cluster_key": key,
            "config_key": cfg.get("cluster_key", ""),
            "cluster_name": cfg.get("cluster_name") or old.get("cluster_name", ""),
            "z": fmt(z, 4),
            "nH_1e22": fmt(result.get("nH_1e22_cm2") or old.get("nH_1e22")),
            "M500_1e14_msun": fmt(m500_1e14),
            "R500_arcsec": fmt(old.get("R500_arcsec")),
            "R500_Mpc": fmt(old.get("R500_Mpc")),
            "Tx_keV": fmt(tx),
            "Tx_err_lo": fmt(tx_lo),
            "Tx_err_hi": fmt(tx_hi),
            "abundance_solar": fmt(result.get("abundance_solar") or old.get("abundance_solar")),
            "apec_norm": fmt(result.get("apec_norm") or old.get("apec_norm")),
            "Lx_bol_1e44_erg_s": fmt((as_float(result.get("bolometric_luminosity_unabsorbed_erg_s")) or 0) / 1e44 if result else old.get("Lx_bol_1e44_erg_s")),
            "Lx_soft_1e44_erg_s": fmt((as_float(result.get("soft_luminosity_unabsorbed_erg_s")) or 0) / 1e44 if result else old.get("Lx_soft_1e44_erg_s")),
            "flux_bol_1e12_erg_s_cm2": fmt((as_float(result.get("bolometric_flux_unabsorbed_erg_s_cm2")) or 0) / 1e-12 if result else old.get("flux_bol_1e12_erg_s_cm2")),
            "rstat": fmt(result.get("rstat") or old.get("rstat")),
            "qval": fmt(result.get("q_value") or result.get("qval") or old.get("qval")),
            "dof": fmt(result.get("dof") or old.get("dof")),
            "n_src_spec": str(len(source_spectra) or old.get("n_src_spec", "")),
            "n_ann_spec": str(len(annulus_spectra) or old.get("n_ann_spec", "")),
            "R_EM": fmt(result.get("r_em_annulus_to_source") or old.get("R_EM")),
            "annulus_rstat": fmt(annulus_fit.get("rstat") or old.get("annulus_rstat")),
            "accept_Tx_keV": fmt(accept_tx),
            "accept_Lx_1e44_erg_s": fmt(acc.get("accept_lbol_1e44") or old.get("accept_Lx_1e44_erg_s")),
            "ratio_Tx_accept": fmt(ratio),
            "method": "blank_sky_XRB_heRenorm" if result else old.get("method", ""),
            "xrb_policy": str(result.get("xrb_policy") or annulus_fit.get("xrb_policy") or old.get("xrb_policy", "")),
            "abundance_policy": str(result.get("abundance_policy") or old.get("abundance_policy", "")),
            "fit_band": str(fit_band),
            "qa_flags": old.get("qa_flags", ""),
            "quality": quality,
            "exclude_from_main_scaling": str(bool(exclude)),
            "exclude_reason": exclude_reason,
            "spectral_status": spectral_status,
            "status": "done" if result_path else "missing_result",
            "pipeline_notes": pipe.get("notes", ""),
            "result_json": str(result_path) if result_path else "",
        })

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    excluded = [row["cluster_key"] for row in rows if row["exclude_from_main_scaling"] == "True"]
    print(f"Wrote {OUTPUT_CSV}")
    print(f"Rows: {len(rows)}")
    print(f"Main sample: {len(rows) - len(excluded)} included, {len(excluded)} excluded")
    print("Excluded:", ", ".join(excluded))


if __name__ == "__main__":
    main()
