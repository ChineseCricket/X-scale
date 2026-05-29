#!/usr/bin/env python3
"""Backfill native Sherpa flux intervals into saved full-R500 JSON products.

This reruns only the Sherpa ``sample_energy_flux`` step from the saved Phase 3
source model and existing spectra. It does not run CIAO repro, merge, source
detection, specextract, blank-sky generation, or a new annulus/source fit.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SUMMARY = Path("output/products/spectral/spectral_summary.csv")
RESULTS_DIR = Path("output/products/spectral")
WORKDIR = Path("/tmp/xscale_native_lx_sampling")


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--workdir", type=Path, default=WORKDIR)
    parser.add_argument("--flux-samples", type=int, default=3000)
    parser.add_argument(
        "--clusters",
        default="",
        help="Comma-separated cluster keys/config keys to process. Default: retained rows flagged native_flux_sampling_missing.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def selected_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    rows = list(csv.DictReader(args.summary.open(newline="")))
    requested = {item.strip() for item in args.clusters.split(",") if item.strip()}
    out: list[dict[str, str]] = []
    for row in rows:
        if requested:
            keys = {row.get("cluster_key", ""), row.get("config_key", "")}
            result_json = Path(row.get("result_json", "")).name.removesuffix("_results.json")
            keys.add(result_json)
            if not (requested & keys):
                continue
        elif not (
            row.get("status") == "done"
            and row.get("exclude_from_main_scaling") == "False"
            and "native_flux_sampling_missing" in row.get("Lx_uncertainty_flag", "")
        ):
            continue
        out.append(row)
    return out


def write_sherpa_script(cluster: str, result: dict[str, Any], script: Path, out_json: Path, samples: int) -> None:
    source_spectra = result.get("source_spectra") or []
    if not source_spectra:
        raise ValueError(f"{cluster}: missing source_spectra")
    missing = [path for path in source_spectra if not Path(path).exists()]
    if missing:
        raise ValueError(f"{cluster}: missing spectrum files: {missing}")

    ann = result.get("annulus_fit") or {}
    scale = as_float(result.get("xrb_area_scale_source_over_annulus")) or 1.0
    n_h = as_float(result.get("nH_1e22_cm2")) or 0.02
    redshift = as_float(result.get("redshift"))
    temperature = as_float(result.get("temperature_keV"))
    abundance = as_float(result.get("abundance_solar")) or 0.3
    norm = as_float(result.get("apec_norm"))
    dl_cm = as_float(result.get("luminosity_distance_cm"))
    if dl_cm is None:
        soft_flux = as_float(result.get("soft_flux_unabsorbed_erg_s_cm2"))
        soft_lum = as_float(result.get("soft_luminosity_unabsorbed_erg_s"))
        if soft_flux and soft_lum:
            dl_cm = math.sqrt(soft_lum / (4.0 * math.pi * soft_flux))
    if None in (redshift, temperature, norm, dl_cm):
        raise ValueError(f"{cluster}: missing redshift/temperature/apec_norm/luminosity distance")

    fit_band = result.get("fit_band_keV") or [0.7, 7.0]
    abundance_policy = result.get("abundance_policy") or "fixed"
    lhb_norm = (as_float(ann.get("lhb_norm")) or 0.0) * scale
    halo_norm = (as_float(ann.get("halo_norm")) or 0.0) * scale
    cxb_norm = (as_float(ann.get("cxb_norm")) or 0.0) * scale
    lhb_k_t = as_float(ann.get("lhb_kT")) or 0.1
    halo_k_t = as_float(ann.get("halo_kT")) or 0.25
    cxb_index = as_float(ann.get("cxb_phoindex")) or 1.4
    source_literal = repr(source_spectra)
    out_json_abs = out_json.resolve()

    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        f'''#!/usr/bin/env sherpa
from sherpa.astro.ui import *
import builtins
import json
import math
import numpy as np

source_spectra = {source_literal}
out_json = {str(out_json_abs)!r}
fit_band = ({float(fit_band[0]):.12g}, {float(fit_band[1]):.12g})
soft_obs = (0.5 / (1.0 + {redshift:.12g}), 2.0 / (1.0 + {redshift:.12g}))
bolo_obs = (0.01 / (1.0 + {redshift:.12g}), builtins.min(100.0 / (1.0 + {redshift:.12g}), 15.0))
dl_cm = {dl_cm:.12g}
flux_samples = {int(samples)}

clean()
set_stat("wstat")
set_method("levmar")

gal_src = xsphabs.gal_src
gal_src.nH = {n_h:.12g}
gal_src.nH.freeze()

lhb_src = xsapec.lhb_src
lhb_src.kT = {lhb_k_t:.12g}
lhb_src.kT.freeze()
lhb_src.Abundanc = 1.0
lhb_src.Abundanc.freeze()
lhb_src.redshift = 0.0
lhb_src.redshift.freeze()
lhb_src.norm = {lhb_norm:.12g}
lhb_src.norm.freeze()
lhb_src.norm.min = 0.0

halo_src = xsapec.halo_src
halo_src.kT = {halo_k_t:.12g}
halo_src.kT.freeze()
halo_src.Abundanc = 1.0
halo_src.Abundanc.freeze()
halo_src.redshift = 0.0
halo_src.redshift.freeze()
halo_src.norm = {halo_norm:.12g}
halo_src.norm.freeze()
halo_src.norm.min = 0.0

cxb_src = xspowerlaw.cxb_src
cxb_src.PhoIndex = {cxb_index:.12g}
cxb_src.PhoIndex.freeze()
cxb_src.norm = {cxb_norm:.12g}
cxb_src.norm.freeze()
cxb_src.norm.min = 0.0

icm_src = xsapec.icm_src
icm_src.kT = {temperature:.12g}
icm_src.kT.min = 0.1
icm_src.kT.max = 50.0
icm_src.Abundanc = {abundance:.12g}
icm_src.Abundanc.min = 0.05
icm_src.Abundanc.max = 1.5
if {abundance_policy!r} == "free_source":
    icm_src.Abundanc.thaw()
else:
    icm_src.Abundanc.freeze()
icm_src.redshift = {redshift:.12g}
icm_src.redshift.freeze()
icm_src.norm = {norm:.12g}
icm_src.norm.min = 0.0

for i, pha in enumerate(source_spectra, start=1):
    load_pha(i, pha)
    try:
        ignore_bad(i)
    except Exception:
        pass
    notice_id(i, fit_band[0], fit_band[1])
    group_counts(i, 1)
    set_source(i, lhb_src + gal_src * (halo_src + cxb_src + icm_src))

def sampled_interval(label, band, best_flux):
    out = {{
        "band": label,
        "method": "sherpa.sample_energy_flux",
        "n_samples_requested": int(flux_samples),
        "n_samples_used": 0,
        "flux_median_erg_s_cm2": None,
        "flux_err_lo_erg_s_cm2": None,
        "flux_err_hi_erg_s_cm2": None,
        "luminosity_median_erg_s": None,
        "luminosity_err_lo_erg_s": None,
        "luminosity_err_hi_erg_s": None,
        "flag": "",
    }}
    try:
        otherids = tuple(range(2, len(source_spectra) + 1))
        vals = sample_energy_flux(
            band[0],
            band[1],
            id=1,
            otherids=otherids,
            model=icm_src,
            num=flux_samples,
            correlated=False,
            numcores=1,
        )
        arr = np.asarray(vals, dtype=float)
        fluxes = arr[:, 0] if arr.ndim > 1 else arr
        if arr.ndim > 1 and arr.shape[1] >= 2:
            clipped = arr[:, -1]
            fluxes = fluxes[clipped == 0]
        fluxes = fluxes[np.isfinite(fluxes) & (fluxes > 0)]
        if fluxes.size < 20:
            raise ValueError(f"only {{fluxes.size}} valid sampled fluxes")
        p16, p50, p84 = np.percentile(fluxes, [16, 50, 84])
        lo = max(float(p50 - p16), 0.0)
        hi = max(float(p84 - p50), 0.0)
        out.update({{
            "n_samples_used": int(fluxes.size),
            "flux_median_erg_s_cm2": float(p50),
            "flux_err_lo_erg_s_cm2": lo,
            "flux_err_hi_erg_s_cm2": hi,
            "luminosity_median_erg_s": float(4.0 * math.pi * dl_cm * dl_cm * p50),
            "luminosity_err_lo_erg_s": float(4.0 * math.pi * dl_cm * dl_cm * lo),
            "luminosity_err_hi_erg_s": float(4.0 * math.pi * dl_cm * dl_cm * hi),
        }})
    except Exception as exc:
        out["method"] = "failed"
        out["flag"] = f"sample_energy_flux_failed: {{exc}}"
        out["flux_median_erg_s_cm2"] = float(best_flux)
        out["luminosity_median_erg_s"] = float(4.0 * math.pi * dl_cm * dl_cm * best_flux)
    return out

soft_flux = float(calc_energy_flux(soft_obs[0], soft_obs[1], model=icm_src))
bolo_flux = float(calc_energy_flux(bolo_obs[0], bolo_obs[1], model=icm_src))
payload = {{
    "cluster_key": {cluster!r},
    "soft_flux_recomputed_erg_s_cm2": soft_flux,
    "bolometric_flux_recomputed_erg_s_cm2": bolo_flux,
    "flux_uncertainty": {{
        "soft": sampled_interval("soft", soft_obs, soft_flux),
        "bolometric": sampled_interval("bolometric", bolo_obs, bolo_flux),
    }},
}}
with open(out_json, "w") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
print(json.dumps(payload, indent=2, sort_keys=True))
'''
    )


def run_sherpa(script: Path, cwd: Path) -> dict[str, Any]:
    sherpa = shutil.which("sherpa")
    if sherpa is None:
        raise SystemExit("sherpa not found; source CIAO before running this script")
    subprocess.run([sherpa, "-n", "-b", str(script.resolve())], cwd=cwd, check=True)
    out_json = script.with_name(script.name.replace(".py", "_native_flux.json"))
    return json.loads(out_json.read_text())


def patch_result_json(path: Path, payload: dict[str, Any]) -> None:
    result = json.loads(path.read_text())
    flux_uncertainty = payload.get("flux_uncertainty") or {}
    for band in ("soft", "bolometric"):
        entry = flux_uncertainty.get(band) or {}
        if entry.get("method") != "sherpa.sample_energy_flux":
            raise ValueError(f"{path}: {band} sampling failed: {entry.get('flag')}")
        if as_float(entry.get("luminosity_err_lo_erg_s")) is None or as_float(entry.get("luminosity_err_hi_erg_s")) is None:
            raise ValueError(f"{path}: {band} interval missing luminosity errors")
    result["flux_uncertainty"] = flux_uncertainty
    result["lx_uncertainty_method"] = "sherpa.sample_energy_flux"
    result["native_flux_sampling_note"] = (
        "Backfilled by src/03_scaling/backfill_native_lx_uncertainties.py from saved full-R500 source model; "
        "no CIAO repro, merge, source detection, or spectral extraction was rerun."
    )
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def main() -> None:
    args = parse_args()
    rows = selected_rows(args)
    if not rows:
        print("No rows selected.")
        return
    print(f"Selected {len(rows)} clusters:")
    for row in rows:
        print(f"  {row['cluster_key']} -> {row['result_json']}")
    if args.dry_run:
        return

    args.workdir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        cluster = row["cluster_key"]
        result_path = Path(row["result_json"])
        if not result_path.is_absolute():
            result_path = Path.cwd() / result_path
        result = json.loads(result_path.read_text())
        cluster_work = args.workdir / result_path.name.removesuffix("_results.json")
        cluster_work.mkdir(parents=True, exist_ok=True)
        script = cluster_work / f"{result_path.name.removesuffix('_results.json')}_native_flux.py"
        out_json = script.with_name(script.name.replace(".py", "_native_flux.json"))
        write_sherpa_script(cluster, result, script, out_json, args.flux_samples)
        print(f"[run] {cluster}")
        payload = run_sherpa(script, cluster_work)
        patch_result_json(result_path, payload)
        soft = payload["flux_uncertainty"]["soft"]
        bolo = payload["flux_uncertainty"]["bolometric"]
        print(
            f"[ok] {cluster}: soft n={soft['n_samples_used']}, "
            f"bolometric n={bolo['n_samples_used']}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise
