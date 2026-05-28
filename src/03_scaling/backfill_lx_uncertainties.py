#!/usr/bin/env python3
"""Backfill Lx uncertainty metadata into existing spectral result JSON files.

Future spectral reruns write native Sherpa ``sample_energy_flux`` intervals.
This helper gives the current formal JSON products explicit uncertainty
provenance using the saved confidence intervals on ``icm_src.kT`` and
``icm_src.norm`` when native flux samples are absent.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


RESULTS_DIR = Path("output/products/spectral")


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def fallback_interval(result: dict[str, Any], luminosity_key: str) -> dict[str, Any]:
    central = as_float(result.get(luminosity_key))
    ci = result.get("confidence_intervals") or {}
    kt_ci = ci.get("icm_src.kT") or {}
    norm_ci = ci.get("icm_src.norm") or {}
    kt = abs(as_float(kt_ci.get("best")) or as_float(result.get("temperature_keV")) or 0.0)
    norm = abs(as_float(norm_ci.get("best")) or as_float(result.get("apec_norm")) or 0.0)
    kt_lo = abs(as_float(kt_ci.get("lower_delta_1sigma")) or 0.0)
    kt_hi = abs(as_float(kt_ci.get("upper_delta_1sigma")) or 0.0)
    norm_lo = abs(as_float(norm_ci.get("lower_delta_1sigma")) or 0.0)
    norm_hi = abs(as_float(norm_ci.get("upper_delta_1sigma")) or 0.0)
    out = {
        "method": "confidence_interval_parameter_fallback",
        "luminosity_median_erg_s": central,
        "luminosity_err_lo_erg_s": None,
        "luminosity_err_hi_erg_s": None,
        "flag": "native_flux_sampling_missing",
    }
    if central and kt > 0 and norm > 0 and (kt_lo or kt_hi or norm_lo or norm_hi):
        frac_lo = math.hypot(norm_lo / norm, 0.5 * kt_lo / kt)
        frac_hi = math.hypot(norm_hi / norm, 0.5 * kt_hi / kt)
        out["luminosity_err_lo_erg_s"] = central * frac_lo
        out["luminosity_err_hi_erg_s"] = central * frac_hi
    else:
        out["method"] = "missing"
        out["flag"] = "lx_uncertainty_unavailable"
    return out


def main() -> None:
    changed = 0
    for path in sorted(RESULTS_DIR.glob("*_results.json")):
        if "_r500_" in path.name:
            continue
        result = json.loads(path.read_text())
        uncertainty = result.setdefault("flux_uncertainty", {})
        updated = False
        if not uncertainty.get("soft"):
            uncertainty["soft"] = fallback_interval(result, "soft_luminosity_unabsorbed_erg_s")
            updated = True
        if not uncertainty.get("bolometric"):
            uncertainty["bolometric"] = fallback_interval(result, "bolometric_luminosity_unabsorbed_erg_s")
            updated = True
        if updated:
            methods = {entry.get("method", "") for entry in uncertainty.values() if isinstance(entry, dict)}
            result["lx_uncertainty_method"] = ";".join(sorted(method for method in methods if method))
            path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            changed += 1
            print(f"Backfilled {path}")
    print(f"Backfilled Lx uncertainty metadata in {changed} result files")


if __name__ == "__main__":
    main()
