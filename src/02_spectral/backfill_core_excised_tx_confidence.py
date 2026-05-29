#!/usr/bin/env python3
"""Backfill core-excised T_X confidence intervals without changing best fits."""

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


SUMMARY = Path("output/products/spectral/spectral_summary_core_excised.csv")
RESULTS_DIR = Path("output/products/spectral/core_excised")
WORK_DIR = Path("tmp/core_excised_tx_confidence")
EXPECTED_INCLUDED = 18
TX_REL_TOL = 1.0e-3
NORM_REL_TOL = 1.0e-3
STAT_ABS_TOL = 0.1


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def rel_delta(new: float | None, old: float | None) -> float:
    if new is None or old is None:
        return math.inf
    return abs(new - old) / max(abs(old), 1.0e-30)


def slug_key(key: str) -> str:
    return key.replace(".", "_").replace("-", "_").replace("+", "_")


def load_included(summary: Path) -> list[dict[str, str]]:
    with summary.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    included = [row for row in rows if row.get("exclude_from_main_scaling") == "False"]
    if len(included) != EXPECTED_INCLUDED:
        raise SystemExit(f"Expected {EXPECTED_INCLUDED} included clusters, found {len(included)}")
    return included


def result_path_for(row: dict[str, str], results_dir: Path) -> Path:
    from_summary = Path(row.get("result_json", ""))
    if from_summary.exists():
        return from_summary
    candidate = results_dir / f"{slug_key(row['cluster_key'])}_results.json"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"No result JSON for {row['cluster_key']}")


def literal(value: Any) -> str:
    return repr(value)


def write_sherpa_script(cluster: str, result: dict[str, Any], script: Path, out_json: Path) -> None:
    fit_band = result.get("fit_band_keV") or [0.7, 7.0]
    annulus = result.get("annulus_fit") or {}
    area_scale = as_float(result.get("xrb_area_scale_source_over_annulus"))
    if area_scale is None:
        raise ValueError("missing xrb_area_scale_source_over_annulus")
    n_h = as_float(result.get("nH_1e22_cm2"))
    redshift = as_float(result.get("redshift"))
    temperature = as_float(result.get("temperature_keV"))
    norm = as_float(result.get("apec_norm"))
    abundance = as_float(result.get("abundance_solar")) or 0.3
    if None in (n_h, redshift, temperature, norm):
        raise ValueError("missing one of nH/redshift/temperature/apec_norm")

    lhb_norm = (as_float(annulus.get("lhb_norm")) or 0.0) * area_scale
    halo_norm = (as_float(annulus.get("halo_norm")) or 0.0) * area_scale
    cxb_norm = (as_float(annulus.get("cxb_norm")) or 0.0) * area_scale
    halo_k_t = as_float(annulus.get("halo_kT")) or 0.25
    cxb_index = as_float(annulus.get("cxb_phoindex")) or 1.4
    lhb_k_t = as_float(annulus.get("lhb_kT")) or 0.1
    abundance_policy = result.get("abundance_policy") or "fixed"
    source_spectra = result.get("source_spectra") or []
    if not source_spectra:
        raise ValueError("missing source_spectra")

    script.parent.mkdir(parents=True, exist_ok=True)
    out_json_abs = out_json.resolve()
    script.write_text(
        f'''#!/usr/bin/env sherpa
from sherpa.astro.ui import *
import json
import math

source_spectra = {literal(source_spectra)}
out_json = {str(out_json_abs)!r}
fit_band = ({float(fit_band[0]):.12g}, {float(fit_band[1]):.12g})
abundance_policy = {abundance_policy!r}

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
icm_src.Abundanc = {abundance:.12g}
icm_src.Abundanc.min = 0.05
icm_src.Abundanc.max = 1.5
if abundance_policy == "free_source":
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

fit()
fit_result = get_fit_results()

conf_error = None
conf_payload = {{}}
try:
    conf(icm_src.kT)
    conf_result = get_conf_results()
    for pname, pval, pmin, pmax in zip(
        conf_result.parnames,
        conf_result.parvals,
        conf_result.parmins,
        conf_result.parmaxes,
    ):
        conf_payload[str(pname)] = {{
            "best": None if pval is None else float(pval),
            "lower_delta_1sigma": None if pmin is None else float(pmin),
            "upper_delta_1sigma": None if pmax is None else float(pmax),
        }}
except Exception as exc:
    conf_error = str(exc)

payload = {{
    "cluster_key": {cluster!r},
    "temperature_keV": float(icm_src.kT.val),
    "apec_norm": float(icm_src.norm.val),
    "abundance_solar": float(icm_src.Abundanc.val),
    "statval": float(fit_result.statval),
    "dof": int(fit_result.dof),
    "rstat": None if getattr(fit_result, "rstat", None) is None else float(fit_result.rstat),
    "q_value": None if getattr(fit_result, "qval", None) is None else float(fit_result.qval),
    "confidence_intervals": conf_payload,
    "conf_error": conf_error,
}}
with open(out_json, "w") as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
print(json.dumps(payload, indent=2, sort_keys=True))
'''
    )


def run_sherpa(script: Path, cwd: Path) -> None:
    sherpa = shutil.which("sherpa")
    if sherpa is None:
        raise SystemExit("sherpa not found; source CIAO before running this script")
    subprocess.run([sherpa, "-n", "-b", str(script.resolve())], cwd=cwd, check=True)


def validate_confidence(cluster: str, original: dict[str, Any], conf: dict[str, Any]) -> dict[str, Any]:
    kt_old = as_float(original.get("temperature_keV"))
    norm_old = as_float(original.get("apec_norm"))
    stat_old = as_float(original.get("statval"))
    kt_new = as_float(conf.get("temperature_keV"))
    norm_new = as_float(conf.get("apec_norm"))
    stat_new = as_float(conf.get("statval"))

    failures: list[str] = []
    if rel_delta(kt_new, kt_old) > TX_REL_TOL:
        failures.append(f"temperature changed by {rel_delta(kt_new, kt_old):.3g}")
    if rel_delta(norm_new, norm_old) > NORM_REL_TOL:
        failures.append(f"apec_norm changed by {rel_delta(norm_new, norm_old):.3g}")
    if stat_old is None or stat_new is None or abs(stat_new - stat_old) > STAT_ABS_TOL:
        delta = math.inf if stat_old is None or stat_new is None else abs(stat_new - stat_old)
        failures.append(f"statval changed by {delta:.3g}")
    if conf.get("conf_error"):
        failures.append(f"conf failed: {conf['conf_error']}")

    ci = (conf.get("confidence_intervals") or {}).get("icm_src.kT") or {}
    lo = as_float(ci.get("lower_delta_1sigma"))
    hi = as_float(ci.get("upper_delta_1sigma"))
    best = as_float(ci.get("best"))
    if lo is None or hi is None:
        failures.append("missing icm_src.kT confidence interval")
    elif not (lo < 0.0 and hi > 0.0):
        failures.append(f"non-bracketing interval lo={lo} hi={hi}")
    if best is not None and kt_old is not None and rel_delta(best, kt_old) > TX_REL_TOL:
        failures.append(f"confidence best changed by {rel_delta(best, kt_old):.3g}")

    if failures:
        raise RuntimeError(f"{cluster}: " + "; ".join(failures))
    return {
        "best": best if best is not None else kt_old,
        "lower_delta_1sigma": lo,
        "upper_delta_1sigma": hi,
    }


def merge_result(path: Path, confidence_entry: dict[str, Any]) -> None:
    with path.open() as handle:
        result = json.load(handle)
    ci = result.setdefault("confidence_intervals", {})
    ci["icm_src.kT"] = confidence_entry
    result["temperature_err_lo_keV"] = abs(float(confidence_entry["lower_delta_1sigma"]))
    result["temperature_err_hi_keV"] = abs(float(confidence_entry["upper_delta_1sigma"]))
    result["tx_confidence_method"] = "sherpa.conf icm_src.kT"
    result["tx_confidence_status"] = "accepted_without_best_fit_change"
    with path.open("w") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    parser.add_argument("--cluster", action="append", help="Limit to one or more cluster keys.")
    parser.add_argument("--dry-run", action="store_true", help="Write scripts but do not run Sherpa or edit JSON.")
    parser.add_argument("--force", action="store_true", help="Recompute even if a valid Tx interval is already present.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    included = load_included(args.summary)
    wanted = set(args.cluster or [])
    rows = [row for row in included if not wanted or row["cluster_key"] in wanted]
    if wanted and len(rows) != len(wanted):
        found = {row["cluster_key"] for row in rows}
        raise SystemExit(f"Requested clusters not included: {', '.join(sorted(wanted - found))}")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    failures: dict[str, str] = {}
    accepted: list[str] = []

    for row in rows:
        cluster = row["cluster_key"]
        path = result_path_for(row, args.results_dir)
        with path.open() as handle:
            result = json.load(handle)
        existing = result.get("confidence_intervals", {}).get("icm_src.kT") or {}
        if (
            not args.force
            and as_float(existing.get("lower_delta_1sigma")) is not None
            and as_float(existing.get("upper_delta_1sigma")) is not None
        ):
            print(f"[skip] {cluster}: existing icm_src.kT interval")
            accepted.append(cluster)
            continue

        cluster_work = args.work_dir / slug_key(cluster)
        cluster_work.mkdir(parents=True, exist_ok=True)
        script = cluster_work / f"{slug_key(cluster)}_tx_confidence.py"
        conf_json = cluster_work / f"{slug_key(cluster)}_tx_confidence.json"
        try:
            write_sherpa_script(cluster, result, script, conf_json)
            if args.dry_run:
                print(f"[dry-run] {cluster}: wrote {script}")
                continue
            run_sherpa(script, cluster_work)
            with conf_json.open() as handle:
                conf_result = json.load(handle)
            confidence_entry = validate_confidence(cluster, result, conf_result)
            merge_result(path, confidence_entry)
            accepted.append(cluster)
            print(
                f"[ok] {cluster}: "
                f"-{abs(confidence_entry['lower_delta_1sigma']):.4g}/"
                f"+{abs(confidence_entry['upper_delta_1sigma']):.4g} keV"
            )
        except Exception as exc:
            failures[cluster] = str(exc)
            print(f"[fail] {cluster}: {exc}", file=sys.stderr)

    report = {
        "accepted": accepted,
        "failures": failures,
        "n_accepted": len(accepted),
        "n_failures": len(failures),
    }
    report_path = args.work_dir / "backfill_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"[info] report: {report_path}")
    if failures:
        raise SystemExit(f"{len(failures)} confidence backfills failed")


if __name__ == "__main__":
    main()
