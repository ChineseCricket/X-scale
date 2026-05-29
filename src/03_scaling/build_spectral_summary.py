#!/usr/bin/env python3
"""Build the canonical full-R500 spectral table for Phase 4 scaling.

This table supersedes the older ``spectral_twostep_summary.csv`` as the
scaling input.  Static cluster metadata come from ``configs/cluster_table.csv``;
latest spectral quantities come from ``output/products/spectral/*_results.json``;
quality and exclusion decisions come from ``memory/pipeline_status.csv``.
"""

from __future__ import annotations

import csv
import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np


PIPELINE_STATUS = Path("memory/pipeline_status.csv")
CLUSTER_TABLE = Path("configs/cluster_table.csv")
M500_REFERENCE = Path("configs/m500_reference.csv")
ACCEPT_REFERENCE = Path("configs/accept_reference.csv")
LEGACY_SUMMARY = Path("output/products/spectral/spectral_twostep_summary.csv")
RESULTS_DIR = Path("output/products/spectral")
OUTPUT_CSV = Path("output/products/spectral/spectral_summary.csv")

H0 = 70.0
OMEGA_M = 0.3
C_KM_S = 299792.458
G_CGS = 6.67430e-8
MSUN_G = 1.98847e33
MPC_CM = 3.0856775814913673e24

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
    "M500_err_lo",
    "M500_err_hi",
    "M500_err_source",
    "M500_err_note",
    "R500_arcsec",
    "R500_Mpc",
    "R500_err_lo",
    "R500_err_hi",
    "R500_err_source",
    "aperture_label",
    "source_inner_r500",
    "source_outer_r500",
    "Tx_keV",
    "Tx_err_lo",
    "Tx_err_hi",
    "abundance_solar",
    "apec_norm",
    "Lx_bol_1e44_erg_s",
    "Lx_bol_err_lo",
    "Lx_bol_err_hi",
    "Lx_soft_1e44_erg_s",
    "Lx_soft_err_lo",
    "Lx_soft_err_hi",
    "Lx_uncertainty_method",
    "Lx_uncertainty_flag",
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


def e_z(z: float, omega_m: float = OMEGA_M) -> float:
    return math.sqrt(omega_m * (1.0 + z) ** 3 + (1.0 - omega_m))


def critical_density_cgs(z: float, h0: float = H0, omega_m: float = OMEGA_M) -> float:
    h_z = h0 * e_z(z, omega_m) * 1.0e5 / MPC_CM
    return 3.0 * h_z * h_z / (8.0 * math.pi * G_CGS)


def compute_r500_mpc(m500_1e14: float | None, z: float | None) -> float | None:
    if not m500_1e14 or z is None:
        return None
    rho_c = critical_density_cgs(z)
    mass_g = m500_1e14 * 1.0e14 * MSUN_G
    r_cm = (3.0 * mass_g / (4.0 * math.pi * 500.0 * rho_c)) ** (1.0 / 3.0)
    return r_cm / MPC_CM


def angular_diameter_distance_mpc(z: float, ngrid: int = 4096) -> float:
    zz = np.linspace(0.0, z, ngrid + 1)
    inv_e = 1.0 / np.sqrt(OMEGA_M * (1.0 + zz) ** 3 + (1.0 - OMEGA_M))
    comoving = (C_KM_S / H0) * float(np.trapezoid(inv_e, zz))
    return comoving / (1.0 + z)


def angular_radius_arcsec(r_mpc: float | None, z: float | None) -> float | None:
    if r_mpc is None or z is None:
        return None
    return r_mpc / angular_diameter_distance_mpc(z) * 206265.0


def r500_errors(
    r500_mpc: float | None,
    r500_arcsec: float | None,
    m500: float | None,
    m500_lo: float | None,
    m500_hi: float | None,
) -> tuple[float | None, float | None, float | None, float | None]:
    if not r500_mpc or not r500_arcsec or not m500:
        return None, None, None, None
    frac_lo = (m500_lo / m500 / 3.0) if m500_lo else None
    frac_hi = (m500_hi / m500 / 3.0) if m500_hi else None
    return (
        r500_mpc * frac_lo if frac_lo is not None else None,
        r500_mpc * frac_hi if frac_hi is not None else None,
        r500_arcsec * frac_lo if frac_lo is not None else None,
        r500_arcsec * frac_hi if frac_hi is not None else None,
    )


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


def get_indexed(index: dict[str, dict[str, str]], key: str) -> dict[str, str]:
    for form in key_forms(key):
        if form in index:
            return index[form]
    return {}


def interval_from_result(
    result: dict[str, Any],
    band: str,
    central_lum: float | None,
) -> tuple[float | None, float | None, str, str]:
    entry = (result.get("flux_uncertainty") or {}).get(band) or {}
    lo = as_float(entry.get("luminosity_err_lo_erg_s"))
    hi = as_float(entry.get("luminosity_err_hi_erg_s"))
    method = str(entry.get("method") or result.get("lx_uncertainty_method") or "")
    flag = str(entry.get("flag") or "")
    if lo is not None and hi is not None:
        return lo / 1.0e44, hi / 1.0e44, method or "sherpa.sample_energy_flux", flag

    ci = result.get("confidence_intervals") or {}
    kt_ci = ci.get("icm_src.kT") or {}
    norm_ci = ci.get("icm_src.norm") or {}
    kt = abs(as_float(kt_ci.get("best")) or as_float(result.get("temperature_keV")) or 0.0)
    norm = abs(as_float(norm_ci.get("best")) or as_float(result.get("apec_norm")) or 0.0)
    kt_lo = abs(as_float(kt_ci.get("lower_delta_1sigma")) or 0.0)
    kt_hi = abs(as_float(kt_ci.get("upper_delta_1sigma")) or 0.0)
    norm_lo = abs(as_float(norm_ci.get("lower_delta_1sigma")) or 0.0)
    norm_hi = abs(as_float(norm_ci.get("upper_delta_1sigma")) or 0.0)
    if central_lum and kt > 0 and norm > 0 and (kt_lo or kt_hi or norm_lo or norm_hi):
        kt_frac_lo = kt_lo / kt
        kt_frac_hi = kt_hi / kt
        norm_frac_lo = norm_lo / norm
        norm_frac_hi = norm_hi / norm
        # APEC luminosity is linear in norm and weakly kT-dependent; this is a
        # conservative JSON-only fallback until native flux sampling exists.
        frac_lo = math.hypot(norm_frac_lo, 0.5 * kt_frac_lo)
        frac_hi = math.hypot(norm_frac_hi, 0.5 * kt_frac_hi)
        return (
            central_lum / 1.0e44 * frac_lo,
            central_lum / 1.0e44 * frac_hi,
            "confidence_interval_parameter_fallback",
            "native_flux_sampling_missing",
        )
    return None, None, method or "missing", flag or "lx_uncertainty_unavailable"


def find_result_json(cluster_key: str, results_dir: Path) -> Path | None:
    for form in key_forms(cluster_key):
        path = results_dir / f"{slug_key(form)}_results.json"
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=RESULTS_DIR,
        help="Directory containing per-cluster *_results.json files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_CSV,
        help="Output spectral summary CSV.",
    )
    parser.add_argument(
        "--default-aperture-label",
        default="full_R500",
        help="Aperture label to use when a result JSON lacks aperture metadata.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_dir = args.results_dir
    output_csv = args.output
    use_legacy_values = results_dir == RESULTS_DIR

    pipeline = read_pipeline_status(PIPELINE_STATUS)
    configs = index_rows(read_csv(CLUSTER_TABLE))
    m500_ref = index_rows(read_csv(M500_REFERENCE)) if M500_REFERENCE.exists() else {}
    accept = index_rows(read_csv(ACCEPT_REFERENCE))
    legacy = index_rows(read_csv(LEGACY_SUMMARY)) if use_legacy_values and LEGACY_SUMMARY.exists() else {}

    rows: list[dict[str, str]] = []
    for pipe in pipeline:
        key = pipe["cluster_key"]
        cfg = get_indexed(configs, key)
        old = get_indexed(legacy, key)
        acc = get_indexed(accept, key)
        mass_ref = get_indexed(m500_ref, key) or get_indexed(m500_ref, cfg.get("cluster_key", ""))
        result_path = find_result_json(key, results_dir)
        result = load_json(result_path)

        z = as_float(cfg.get("redshift")) or as_float(old.get("z"))
        m500_1e14 = (
            as_float(mass_ref.get("m500_1e14_msun_h70"))
            or ((as_float(cfg.get("m500_physical_msun_h70")) or 0.0) / 1e14)
            or as_float(old.get("M500_1e14_msun"))
        )
        m500_lo = as_float(mass_ref.get("m500_err_lo"))
        m500_hi = as_float(mass_ref.get("m500_err_hi"))
        r500_mpc = compute_r500_mpc(m500_1e14, z)
        r500_arcsec = angular_radius_arcsec(r500_mpc, z)
        r500_lo_mpc, r500_hi_mpc, r500_lo_arcsec, r500_hi_arcsec = r500_errors(
            r500_mpc, r500_arcsec, m500_1e14, m500_lo, m500_hi
        )

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
        tx_lo = abs(tx_lo) if tx_lo is not None else None
        tx_hi = abs(tx_hi) if tx_hi is not None else None
        accept_tx = as_float(acc.get("accept_tx_kev")) or as_float(old.get("accept_Tx_keV"))
        ratio = (tx / accept_tx) if tx and accept_tx else None
        lx_bol = as_float(result.get("bolometric_luminosity_unabsorbed_erg_s")) if result else None
        lx_soft = as_float(result.get("soft_luminosity_unabsorbed_erg_s")) if result else None
        lx_bol_lo, lx_bol_hi, lx_bol_method, lx_bol_flag = interval_from_result(result, "bolometric", lx_bol)
        lx_soft_lo, lx_soft_hi, lx_soft_method, lx_soft_flag = interval_from_result(result, "soft", lx_soft)
        lx_methods = sorted({item for item in (lx_bol_method, lx_soft_method) if item})
        lx_flags = sorted({item for item in (lx_bol_flag, lx_soft_flag) if item})

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
        qa_flags = result.get("qa_flags") or old.get("qa_flags", "")
        if isinstance(qa_flags, list):
            qa_flags = ";".join(str(flag) for flag in qa_flags)
        source_inner = as_float(result.get("source_inner_r500"))
        source_outer = as_float(result.get("source_outer_r500"))
        if use_legacy_values:
            source_inner = 0.0 if source_inner is None else source_inner
            source_outer = 1.0 if source_outer is None else source_outer

        rows.append({
            "cluster_key": key,
            "config_key": cfg.get("cluster_key", ""),
            "cluster_name": cfg.get("cluster_name") or old.get("cluster_name", ""),
            "z": fmt(z, 4),
            "nH_1e22": fmt(result.get("nH_1e22_cm2") or old.get("nH_1e22")),
            "M500_1e14_msun": fmt(m500_1e14),
            "M500_err_lo": fmt(m500_lo),
            "M500_err_hi": fmt(m500_hi),
            "M500_err_source": mass_ref.get("m500_err_source", ""),
            "M500_err_note": mass_ref.get("m500_err_note", ""),
            "R500_arcsec": fmt(r500_arcsec),
            "R500_Mpc": fmt(r500_mpc),
            "R500_err_lo": fmt(r500_lo_arcsec),
            "R500_err_hi": fmt(r500_hi_arcsec),
            "R500_err_source": "propagated_from_M500_err; delta_R500/R500=(1/3)delta_M500/M500" if r500_lo_arcsec or r500_hi_arcsec else "",
            "aperture_label": str(result.get("aperture_label") or args.default_aperture_label),
            "source_inner_r500": fmt(source_inner),
            "source_outer_r500": fmt(source_outer),
            "Tx_keV": fmt(tx),
            "Tx_err_lo": fmt(tx_lo),
            "Tx_err_hi": fmt(tx_hi),
            "abundance_solar": fmt(result.get("abundance_solar") or old.get("abundance_solar")),
            "apec_norm": fmt(result.get("apec_norm") or old.get("apec_norm")),
            "Lx_bol_1e44_erg_s": fmt(lx_bol / 1e44 if lx_bol is not None else old.get("Lx_bol_1e44_erg_s")),
            "Lx_bol_err_lo": fmt(lx_bol_lo),
            "Lx_bol_err_hi": fmt(lx_bol_hi),
            "Lx_soft_1e44_erg_s": fmt(lx_soft / 1e44 if lx_soft is not None else old.get("Lx_soft_1e44_erg_s")),
            "Lx_soft_err_lo": fmt(lx_soft_lo),
            "Lx_soft_err_hi": fmt(lx_soft_hi),
            "Lx_uncertainty_method": ";".join(lx_methods),
            "Lx_uncertainty_flag": ";".join(lx_flags),
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
            "qa_flags": str(qa_flags),
            "quality": quality,
            "exclude_from_main_scaling": str(bool(exclude)),
            "exclude_reason": exclude_reason,
            "spectral_status": spectral_status,
            "status": "done" if result_path else "missing_result",
            "pipeline_notes": pipe.get("notes", ""),
            "result_json": str(result_path) if result_path else "",
        })

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    excluded = [row["cluster_key"] for row in rows if row["exclude_from_main_scaling"] == "True"]
    print(f"Wrote {output_csv}")
    print(f"Rows: {len(rows)}")
    print(f"Main sample: {len(rows) - len(excluded)} included, {len(excluded)} excluded")
    print("Excluded:", ", ".join(excluded))


if __name__ == "__main__":
    main()
