#!/usr/bin/env python3
"""Phase 3 B+C spectral fitting: blank-sky background + XRB model + joint fit.

Implements the pipeline validated on Abell_383 (T_X=4.93 keV vs ACCEPT=3.93):
1. Generate blank-sky event files (CIAO blanksky) per ObsID
2. Extract source (0-1 R500) and annulus (1.2-1.8 R500) spectra with blank-sky bkg
3. Renormalize blank-sky AREASCAL in 9.5-12 keV particle-dominated band
4. Two-step Sherpa fit: annulus XRB → source ICM with frozen XRB
5. Copy results to output/ per CLAUDE.md conventions

Adapted from weiwwqeo_scripts/src/02_spectral/fit_spectral_joint.py
with our infrastructure (postproces_cluster.py, beta_model_profile.py).
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from postproces_cluster import (
    CLUSTER_TABLE_PATH,
    ClusterConfig,
    angular_radius_arcsec,
    compute_r500_mpc,
    default_cluster_dir,
    discover_individual_evt2,
    find_xray_peak_center,
    load_cluster_configs_from_table,
    load_point_source_masks,
    luminosity_distance_cm,
    obsid_from_evt_path,
    resolve_cluster_config,
    run,
    sky_xy_from_event_wcs,
    source_masks_for_event,
)

# --- Constants ---
DEFAULT_H0 = 70.0
DEFAULT_OMEGA_M = 0.3
DEFAULT_FIT_BAND = (0.7, 7.0)
DEFAULT_SOURCE_OUTER_R500 = 1.0
DEFAULT_ANNULUS_INNER_R500 = 1.2
DEFAULT_ANNULUS_OUTER_R500 = 1.8
DEFAULT_LHB_KT = 0.10
DEFAULT_LHB_NORM = 5.0e-6
DEFAULT_HALO_KT = 0.25
DEFAULT_HALO_NORM_INIT = 1.0e-6
DEFAULT_CXB_INDEX = 1.40
DEFAULT_CXB_NORM_INIT = 1.0e-5
DEFAULT_ICM_ANN_KT_FACTOR = 0.7
DEFAULT_ABUNDANCE = 0.3
DEFAULT_BLANKSKY_RENORM_BAND = (9.5, 12.0)
DEFAULT_POINT_SOURCE_SIGMA_MIN = 3.0
DEFAULT_POINT_SOURCE_RADIUS_SCALE = 1.5
DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX = 3.0
DEFAULT_POINT_SOURCE_SKIP_CENTER_R500 = 0.15
DEFAULT_XRAY_PEAK_SEARCH_ARCSEC = 60.0


# --- Data classes ---
@dataclass
class SpectrumSet:
    obsid: str
    source_pi: str | None
    annulus_pi: str | None
    source_region: str
    annulus_region: str
    evt_file: str
    blanksky_file: str | None


@dataclass
class BackgroundRenormDiagnostic:
    obsid: str
    spectrum_kind: str
    original_source_pi: str
    renormalized_source_pi: str
    original_background_pi: str
    renormalized_background_pi: str
    band_keV: list[float]
    source_counts: float
    background_counts: float
    predicted_background_counts: float
    source_over_predicted_background: float
    old_background_areascale: float
    new_background_areascale: float


# --- Blank-sky event generation ---
def run_blanksky_for_obsids(
    evt2_by_obsid: dict[str, Path], outdir: Path, require: bool = False
) -> dict[str, Path]:
    """Generate blank-sky event files for each ObsID using CIAO blanksky."""
    outdir.mkdir(parents=True, exist_ok=True)
    blank_by_obsid: dict[str, Path] = {}
    for obsid, evt in evt2_by_obsid.items():
        blank = outdir / f"obs{obsid}_blanksky_evt.fits"
        if not blank.exists():
            cmd = [
                "blanksky",
                f"evtfile={evt}",
                f"outfile={blank}",
                "weight_method=particle",
                "bkgparams=default",
                "clobber=yes",
                "mode=h",
            ]
            try:
                run(cmd, cwd=outdir)
            except subprocess.CalledProcessError as exc:
                msg = f"blanksky failed for ObsID {obsid}: {exc}"
                if require:
                    raise SystemExit(msg) from exc
                print(f"[warn] {msg}")
                continue
        blank_by_obsid[obsid] = blank.resolve()
    return blank_by_obsid


def load_existing_blanksky(
    evt2_by_obsid: dict[str, Path], outdir: Path, cluster_dir: Path | None = None, cluster_key: str = ""
) -> dict[str, Path]:
    """Load previously generated blank-sky files from outdir or legacy locations."""
    out: dict[str, Path] = {}
    for obsid in evt2_by_obsid:
        candidates = [outdir / f"obs{obsid}_blanksky_evt.fits"]
        # Legacy location: postprocess_r500/<cluster>_obs<obsid>_blanksky.fits
        if cluster_dir and cluster_key:
            for alt_key in _alt_cluster_keys(cluster_key):
                candidates.append(cluster_dir / "postprocess_r500" / f"{alt_key}_obs{obsid}_blanksky.fits")
        for p in candidates:
            if p.exists():
                out[obsid] = p.resolve()
                break
    return out


# --- Region writing ---
def write_event_region(
    path: Path,
    evt: Path,
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    inner_r500: float,
    outer_r500: float,
    masks: list[Any],
) -> Path:
    """Write a CIAO physical-sky region file for one ObsID."""
    x, y, pix_arcsec = sky_xy_from_event_wcs(evt, center_ra, center_dec)
    r_outer = outer_r500 * r500_arcsec / pix_arcsec
    r_inner = inner_r500 * r500_arcsec / pix_arcsec
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        if inner_r500 > 0:
            f.write(f"annulus({x:.6f},{y:.6f},{r_inner:.6f},{r_outer:.6f})\n")
        else:
            f.write(f"circle({x:.6f},{y:.6f},{r_outer:.6f})\n")
        for sx, sy, sr in source_masks_for_event(evt, masks):
            f.write(f"-circle({sx:.6f},{sy:.6f},{sr:.6f})\n")
    return path.resolve()


# --- Spectral extraction ---
def run_specextract_blanksky(
    cluster_dir: Path,
    evt: Path,
    blank_evt: Path,
    region: Path,
    outroot: Path,
) -> Path | None:
    """Run specextract with blank-sky background."""
    if shutil.which("specextract") is None:
        print("[warn] specextract not found; skipping extraction")
        return None
    cmd = [
        "specextract",
        f"infile={evt}[sky=region({region})]",
        f"bkgfile={blank_evt}[sky=region({region})]",
        f"outroot={outroot}",
        "correctpsf=no",
        "weight=no",
        "bkgresp=no",
        "clobber=yes",
        "mode=h",
    ]
    try:
        run(cmd, cwd=cluster_dir)
    except subprocess.CalledProcessError as exc:
        print(f"[warn] specextract failed for {evt}: {exc}")
        return None
    pi = Path(str(outroot) + ".pi")
    return pi.resolve() if pi.exists() else None


def _alt_cluster_keys(key: str) -> list[str]:
    """Return alternate cluster key forms (dots/dashes <-> underscores)."""
    keys = [key]
    if "." in key or "-" in key or "+" in key:
        # MACSJ0329.7-0211 → MACSJ0329_7_0211
        import re
        keys.append(re.sub(r'[.\-+]', '_', key))
    if "_" in key:
        # MACSJ0329_7_0211 → try MACSJ0329.7-0211
        import re
        # Common patterns: XXX_N_MMMM → XXX.N-MMMM or XXX.N+MMMM
        m = re.match(r'^(.+?)[_](\d)[_-](\d{4})$', key)
        if m:
            keys.append(f"{m.group(1)}.{m.group(2)}-{m.group(3)}")
            keys.append(f"{m.group(1)}.{m.group(2)}+{m.group(3)}")
        # RXJ2129_7_0005 pattern
        m2 = re.match(r'^(RXJ\d+)[_](\d)[_](\d{4})$', key)
        if m2:
            keys.append(f"{m2.group(1)}.{m2.group(2)}+{m2.group(3)}")
            keys.append(f"{m2.group(1)}.{m2.group(2)}-{m2.group(3)}")
    return keys


def _find_spectrum(spectra_dir: Path, cluster_key: str, obsid: str, suffix: str) -> Path | None:
    """Find a spectrum file trying all naming conventions."""
    for key in _alt_cluster_keys(cluster_key):
        p = spectra_dir / f"{key}_obs{obsid}_{suffix}"
        if p.exists():
            return p
    # Last resort: glob for any matching obsid + suffix
    matches = sorted(spectra_dir.glob(f"*_obs{obsid}_{suffix}"))
    return matches[0] if matches else None


def extract_joint_spectra(
    cluster_dir: Path,
    outdir: Path,
    cluster_key: str,
    evt2_by_obsid: dict[str, Path],
    blank_by_obsid: dict[str, Path],
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    masks: list[Any],
    run_specextract: bool,
    ann_inner_r500: float = DEFAULT_ANNULUS_INNER_R500,
    ann_outer_r500: float = DEFAULT_ANNULUS_OUTER_R500,
) -> list[SpectrumSet]:
    """Extract source and annulus spectra for each ObsID with blank-sky bkg."""
    spectra_dir = outdir / "spectra"
    region_dir = outdir / "regions" / "per_obs"
    products: list[SpectrumSet] = []
    for obsid, evt in evt2_by_obsid.items():
        if obsid not in blank_by_obsid:
            print(f"[warn] no blank-sky file for ObsID {obsid}; skipping")
            continue
        blank = blank_by_obsid[obsid]
        src_reg = write_event_region(
            region_dir / f"{cluster_key}_obs{obsid}_src_r500.reg",
            evt, center_ra, center_dec, r500_arcsec,
            0.0, DEFAULT_SOURCE_OUTER_R500, masks,
        )
        ann_reg = write_event_region(
            region_dir / f"{cluster_key}_obs{obsid}_ann_{ann_inner_r500:.1f}_{ann_outer_r500:.1f}r500.reg",
            evt, center_ra, center_dec, r500_arcsec,
            ann_inner_r500, ann_outer_r500, masks,
        )
        src_pattern = f"{cluster_key}_obs{obsid}_src_r500.pi"
        ann_pattern = f"{cluster_key}_obs{obsid}_ann_{ann_inner_r500:.1f}_{ann_outer_r500:.1f}r500.pi"
        if run_specextract:
            src = run_specextract_blanksky(
                cluster_dir, evt, blank, src_reg,
                spectra_dir / f"{cluster_key}_obs{obsid}_src_r500",
            )
            ann = run_specextract_blanksky(
                cluster_dir, evt, blank, ann_reg,
                spectra_dir / f"{cluster_key}_obs{obsid}_ann_{ann_inner_r500:.1f}_{ann_outer_r500:.1f}r500",
            )
        else:
            # Look for existing spectra with all naming conventions
            src_p = _find_spectrum(spectra_dir, cluster_key, obsid, "src_r500.pi")
            ann_p = _find_spectrum(spectra_dir, cluster_key, obsid,
                                   f"ann_{ann_inner_r500:.1f}_{ann_outer_r500:.1f}r500.pi")
            src = src_p.resolve() if src_p else None
            ann = ann_p.resolve() if ann_p else None
            # Legacy: postprocess_r500/<cluster>_obs<obsid>_blanksky_src.pi / _ann.pi
            if src is None:
                for alt_key in _alt_cluster_keys(cluster_key):
                    legacy = cluster_dir / "postprocess_r500" / f"{alt_key}_obs{obsid}_blanksky_src.pi"
                    if legacy.exists():
                        src = legacy.resolve()
                        break
            if ann is None:
                for alt_key in _alt_cluster_keys(cluster_key):
                    legacy = cluster_dir / "postprocess_r500" / f"{alt_key}_obs{obsid}_blanksky_ann.pi"
                    if legacy.exists():
                        ann = legacy.resolve()
                        break
        products.append(SpectrumSet(
            obsid=obsid,
            source_pi=str(src) if src else None,
            annulus_pi=str(ann) if ann else None,
            source_region=str(src_reg),
            annulus_region=str(ann_reg),
            evt_file=str(evt),
            blanksky_file=str(blank),
        ))
    return products


# --- Area computation ---
def approximate_unmasked_area_arcsec2(
    inner_r500: float, outer_r500: float, r500_arcsec: float, masks: list[Any]
) -> float:
    area = math.pi * ((outer_r500 * r500_arcsec) ** 2 - (inner_r500 * r500_arcsec) ** 2)
    for src in masks:
        sep = getattr(src, "separation_arcsec", None)
        rad = getattr(src, "radius_arcsec", 0.0)
        if sep is not None and inner_r500 * r500_arcsec <= sep <= outer_r500 * r500_arcsec:
            area -= math.pi * rad * rad
    return max(area, 1.0)


# --- Wei's 3 key functions ---
def _pha_high_energy_renorm_factor(
    src_pi: Path, bkg_pi: Path, rmf: Path, band: tuple[float, float]
) -> dict[str, float]:
    """Compute blank-sky renormalization factor in particle-dominated band."""
    from astropy.io import fits

    with fits.open(src_pi) as hs, fits.open(bkg_pi) as hb, fits.open(rmf) as hr:
        sdat = hs[1].data
        bdat = hb[1].data
        ebounds = hr["EBOUNDS"].data
        ebounds_by_channel = {
            int(ch): (float(emin), float(emax))
            for ch, emin, emax in zip(ebounds["CHANNEL"], ebounds["E_MIN"], ebounds["E_MAX"])
        }
        energy_mid = np.array([
            0.5 * (ebounds_by_channel[int(ch)][0] + ebounds_by_channel[int(ch)][1])
            for ch in sdat["CHANNEL"]
        ])
        keep = (energy_mid >= band[0]) & (energy_mid <= band[1])
        source_counts = float(np.asarray(sdat["COUNTS"])[keep].sum())
        background_counts = float(np.asarray(bdat["COUNTS"])[keep].sum())
        src_exposure = float(hs[1].header.get("EXPOSURE", 1.0))
        bkg_exposure = float(hb[1].header.get("EXPOSURE", 1.0))
        src_backscal = float(hs[1].header.get("BACKSCAL", 1.0))
        bkg_backscal = float(hb[1].header.get("BACKSCAL", 1.0))
        src_areascale = float(hs[1].header.get("AREASCAL", 1.0))
        bkg_areascale = float(hb[1].header.get("AREASCAL", 1.0))

    scale = (src_exposure * src_backscal * src_areascale) / max(bkg_exposure * bkg_backscal * bkg_areascale, 1e-30)
    predicted_background = background_counts * scale
    factor = source_counts / max(predicted_background, 1e-30)
    return {
        "source_counts": source_counts,
        "background_counts": background_counts,
        "predicted_background_counts": predicted_background,
        "factor": factor,
        "old_background_areascale": bkg_areascale,
    }


def renormalize_blanksky_background_phas(
    spectrum_sets: list[SpectrumSet],
    output_dir: Path,
    band: tuple[float, float] = DEFAULT_BLANKSKY_RENORM_BAND,
) -> tuple[list[SpectrumSet], list[BackgroundRenormDiagnostic]]:
    """Copy spectra and renormalize blank-sky background PHAs in 9.5-12 keV."""
    from astropy.io import fits

    output_dir.mkdir(parents=True, exist_ok=True)
    renorm_sets: list[SpectrumSet] = []
    diagnostics: list[BackgroundRenormDiagnostic] = []

    for spec in spectrum_sets:
        new_spec = SpectrumSet(**asdict(spec))
        for kind, pi_str in (("source", spec.source_pi), ("annulus", spec.annulus_pi)):
            if not pi_str:
                continue
            src_pi = Path(pi_str)
            bkg_pi = src_pi.with_name(src_pi.stem + "_bkg.pi")
            arf = src_pi.with_suffix(".arf")
            rmf = src_pi.with_suffix(".rmf")
            if not (src_pi.exists() and bkg_pi.exists() and arf.exists() and rmf.exists()):
                continue
            diag = _pha_high_energy_renorm_factor(src_pi, bkg_pi, rmf, band)
            factor = max(diag["factor"], 1e-6)
            suffix = f"_he{band[0]:g}_{band[1]:g}keV".replace(".", "p")
            new_src = output_dir / f"{src_pi.stem}{suffix}.pi"
            new_bkg = output_dir / f"{src_pi.stem}{suffix}_bkg.pi"
            new_arf = output_dir / arf.name
            new_rmf = output_dir / rmf.name
            shutil.copy2(src_pi, new_src)
            shutil.copy2(bkg_pi, new_bkg)
            shutil.copy2(arf, new_arf)
            shutil.copy2(rmf, new_rmf)
            with fits.open(new_bkg, mode="update") as hb:
                old_area = float(hb[1].header.get("AREASCAL", 1.0))
                hb[1].header["AREASCAL"] = old_area / factor
            with fits.open(new_src, mode="update") as hs:
                hs[1].header["BACKFILE"] = new_bkg.name
                hs[1].header["ANCRFILE"] = new_arf.name
                hs[1].header["RESPFILE"] = new_rmf.name
            if kind == "source":
                new_spec.source_pi = str(new_src.resolve())
            else:
                new_spec.annulus_pi = str(new_src.resolve())
            diagnostics.append(BackgroundRenormDiagnostic(
                obsid=spec.obsid,
                spectrum_kind=kind,
                original_source_pi=str(src_pi),
                renormalized_source_pi=str(new_src.resolve()),
                original_background_pi=str(bkg_pi),
                renormalized_background_pi=str(new_bkg.resolve()),
                band_keV=[band[0], band[1]],
                source_counts=diag["source_counts"],
                background_counts=diag["background_counts"],
                predicted_background_counts=diag["predicted_background_counts"],
                source_over_predicted_background=factor,
                old_background_areascale=diag["old_background_areascale"],
                new_background_areascale=diag["old_background_areascale"] / factor,
            ))
        renorm_sets.append(new_spec)
    return renorm_sets, diagnostics


def write_joint_sherpa_script(
    script: Path,
    out_json: Path,
    out_plot: Path,
    source_spectra: list[str],
    annulus_spectra: list[str],
    z: float,
    nh_1e22: float,
    dl_cm: float,
    kt_init: float,
    r_em: float,
    xrb_area_scale_source_over_annulus: float,
    xrb_policy: str,
    fit_band: tuple[float, float],
    abundance_policy: str,
) -> None:
    """Write two-step Sherpa script: annulus XRB → source ICM."""
    source_literal = repr(source_spectra)
    ann_literal = repr(annulus_spectra)
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(f'''#!/usr/bin/env sherpa
from sherpa.astro.ui import *
import builtins
import json
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

source_spectra = {source_literal}
annulus_spectra = {ann_literal}
if not source_spectra or not annulus_spectra:
    raise SystemExit("Need both source and annulus spectra")

fit_band = ({fit_band[0]:.8g}, {fit_band[1]:.8g})
soft_obs = ({0.5:.8g} / (1 + {z:.8g}), {2.0:.8g} / (1 + {z:.8g}))
bolo_obs = ({0.01:.8g} / (1 + {z:.8g}), builtins.min({100.0:.8g} / (1 + {z:.8g}), 15.0))
plot_caveat = "WSTAT with blank-sky PHA; plotted residuals are qualitative."
xrb_policy = {xrb_policy!r}
abundance_policy = {abundance_policy!r}

# Step 2pre: rough source-only ICM fit to estimate the source APEC norm.
clean()
set_stat("wstat")
set_method("levmar")

gal_pre = xsphabs.gal_pre
gal_pre.nH = {nh_1e22:.8g}; gal_pre.nH.freeze()
icm_pre = xsapec.icm_pre
icm_pre.kT = {kt_init:.8g}
icm_pre.Abundanc = {DEFAULT_ABUNDANCE:.8g}; icm_pre.Abundanc.freeze()
icm_pre.redshift = {z:.8g}; icm_pre.redshift.freeze()
icm_pre.norm = 1e-3

for i, pha in enumerate(source_spectra, start=1):
    load_pha(i, pha)
    try:
        ignore_bad(i)
    except Exception:
        pass
    notice_id(i, fit_band[0], fit_band[1])
    group_counts(i, 1)
    set_source(i, gal_pre * icm_pre)

fit()
prefit = get_fit_results()
prefit_values = {{
    "temperature_keV": float(icm_pre.kT.val),
    "apec_norm": float(icm_pre.norm.val),
    "statval": float(prefit.statval),
    "dof": int(prefit.dof),
    "rstat": None if getattr(prefit, "rstat", None) is None else float(prefit.rstat),
    "q_value": None if getattr(prefit, "qval", None) is None else float(prefit.qval),
}}

# Step 2a: annulus fit determines XRB normalization with an ICM leakage term.
clean()
set_stat("wstat")
set_method("levmar")

gal_ann = xsphabs.gal_ann
gal_ann.nH = {nh_1e22:.8g}
gal_ann.nH.freeze()

lhb_ann = xsapec.lhb_ann
lhb_ann.kT = {DEFAULT_LHB_KT:.8g}; lhb_ann.kT.freeze()
lhb_ann.kT.min = 0.07; lhb_ann.kT.max = 0.15
lhb_ann.Abundanc = 1.0; lhb_ann.Abundanc.freeze()
lhb_ann.redshift = 0.0; lhb_ann.redshift.freeze()
lhb_ann.norm = {DEFAULT_LHB_NORM:.8g}; lhb_ann.norm.freeze()
lhb_ann.norm.min = 0.0

halo_ann = xsapec.halo_ann
halo_ann.kT = {DEFAULT_HALO_KT:.8g}; halo_ann.kT.freeze()
halo_ann.kT.min = 0.15; halo_ann.kT.max = 0.35
halo_ann.Abundanc = 1.0; halo_ann.Abundanc.freeze()
halo_ann.redshift = 0.0; halo_ann.redshift.freeze()
halo_ann.norm = {DEFAULT_HALO_NORM_INIT:.8g}
halo_ann.norm.min = 0.0

cxb_ann = xspowerlaw.cxb_ann
cxb_ann.PhoIndex = {DEFAULT_CXB_INDEX:.8g}; cxb_ann.PhoIndex.freeze()
cxb_ann.PhoIndex.min = 1.1; cxb_ann.PhoIndex.max = 1.7
cxb_ann.norm = {DEFAULT_CXB_NORM_INIT:.8g}
cxb_ann.norm.min = 0.0

icm_ann = xsapec.icm_ann
icm_ann.kT = builtins.max(0.5, {DEFAULT_ICM_ANN_KT_FACTOR:.8g} * prefit_values["temperature_keV"])
icm_ann.Abundanc = {DEFAULT_ABUNDANCE:.8g}; icm_ann.Abundanc.freeze()
icm_ann.redshift = {z:.8g}; icm_ann.redshift.freeze()
icm_ann.norm = builtins.max(1e-8, {r_em:.8g} * prefit_values["apec_norm"])
icm_ann.norm.freeze()

if xrb_policy == "flexible":
    lhb_ann.kT.thaw()
    lhb_ann.norm.thaw()
    halo_ann.kT.thaw()
    cxb_ann.PhoIndex.thaw()
elif xrb_policy != "fixed_shape":
    raise SystemExit(f"Unknown xrb_policy: {{xrb_policy}}")

for i, pha in enumerate(annulus_spectra, start=1):
    load_pha(i, pha)
    try:
        ignore_bad(i)
    except Exception:
        pass
    notice_id(i, fit_band[0], fit_band[1])
    group_counts(i, 1)
    set_source(i, lhb_ann + gal_ann * (halo_ann + cxb_ann + icm_ann))

fit()
ann_fit = get_fit_results()
ann_values = {{
    "statname": ann_fit.statname,
    "statval": float(ann_fit.statval),
    "dof": int(ann_fit.dof),
    "rstat": None if getattr(ann_fit, "rstat", None) is None else float(ann_fit.rstat),
    "q_value": None if getattr(ann_fit, "qval", None) is None else float(ann_fit.qval),
    "xrb_policy": xrb_policy,
    "lhb_kT": float(lhb_ann.kT.val),
    "lhb_norm": float(lhb_ann.norm.val),
    "halo_kT": float(halo_ann.kT.val),
    "halo_norm": float(halo_ann.norm.val),
    "cxb_phoindex": float(cxb_ann.PhoIndex.val),
    "cxb_norm": float(cxb_ann.norm.val),
    "icm_ann_kT": float(icm_ann.kT.val),
    "icm_ann_norm": float(icm_ann.norm.val),
    "icm_ann_norm_policy": "frozen_to_beta_R_EM_times_source_prefit_norm",
}}
ann_values["n_free_parameters"] = 7 if xrb_policy == "flexible" else 3
ann_values["aic_wstat"] = ann_values["statval"] + 2.0 * ann_values["n_free_parameters"]
ann_values["bic_wstat"] = ann_values["statval"] + ann_values["n_free_parameters"] * math.log({len(annulus_spectra)} * 440.0)

# Step 2b: source fit freezes XRB shape and area-scales XRB normalization.
clean()
set_stat("wstat")
set_method("levmar")

gal_src = xsphabs.gal_src
gal_src.nH = {nh_1e22:.8g}; gal_src.nH.freeze()

lhb_src = xsapec.lhb_src
lhb_src.kT = ann_values["lhb_kT"]; lhb_src.kT.freeze()
lhb_src.Abundanc = 1.0; lhb_src.Abundanc.freeze()
lhb_src.redshift = 0.0; lhb_src.redshift.freeze()
lhb_src.norm = ann_values["lhb_norm"] * {xrb_area_scale_source_over_annulus:.12g}; lhb_src.norm.freeze()

halo_src = xsapec.halo_src
halo_src.kT = ann_values["halo_kT"]; halo_src.kT.freeze()
halo_src.Abundanc = 1.0; halo_src.Abundanc.freeze()
halo_src.redshift = 0.0; halo_src.redshift.freeze()
halo_src.norm = ann_values["halo_norm"] * {xrb_area_scale_source_over_annulus:.12g}; halo_src.norm.freeze()

cxb_src = xspowerlaw.cxb_src
cxb_src.PhoIndex = ann_values["cxb_phoindex"]; cxb_src.PhoIndex.freeze()
cxb_src.norm = ann_values["cxb_norm"] * {xrb_area_scale_source_over_annulus:.12g}; cxb_src.norm.freeze()

icm_src = xsapec.icm_src
icm_src.kT = {kt_init:.8g}
icm_src.Abundanc = {DEFAULT_ABUNDANCE:.8g}; icm_src.Abundanc.freeze()
icm_src.Abundanc.min = 0.05; icm_src.Abundanc.max = 1.5
if abundance_policy == "free_source":
    icm_src.Abundanc.thaw()
elif abundance_policy != "fixed":
    raise SystemExit(f"Unknown abundance_policy: {{abundance_policy}}")
icm_src.redshift = {z:.8g}; icm_src.redshift.freeze()
icm_src.norm = 1e-3

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
conf_values = None
try:
    conf()
    conf_values = get_conf_results()
except Exception as exc:
    print("[warn] conf failed:", exc)

fr = get_fit_results()
soft_flux_unabs = float(calc_energy_flux(soft_obs[0], soft_obs[1], model=icm_src))
bolo_flux_unabs = float(calc_energy_flux(bolo_obs[0], bolo_obs[1], model=icm_src))
dl_cm = {dl_cm:.12g}
soft_lum = 4.0 * math.pi * dl_cm * dl_cm * soft_flux_unabs
bolo_lum = 4.0 * math.pi * dl_cm * dl_cm * bolo_flux_unabs

confidence = {{}}
if conf_values is not None:
    for pname, pval, pmin, pmax in zip(conf_values.parnames, conf_values.parvals, conf_values.parmins, conf_values.parmaxes):
        confidence[str(pname)] = {{
            "best": None if pval is None else float(pval),
            "lower_delta_1sigma": None if pmin is None else float(pmin),
            "upper_delta_1sigma": None if pmax is None else float(pmax),
        }}

qa_flags = []
if getattr(fr, "rstat", None) is not None and fr.rstat > 1.5:
    qa_flags.append("high_reduced_statistic")
if getattr(fr, "qval", None) is not None and fr.qval < 0.01:
    qa_flags.append("low_q_value")
if icm_src.kT.val > 20:
    qa_flags.append("very_high_temperature")
if ann_values["rstat"] is not None and ann_values["rstat"] > 2.0:
    qa_flags.append("annulus_xrb_fit_rstat_gt_2")
if xrb_policy == "flexible":
    qa_flags.append("xrb_shapes_freed_compare_aic_bic_before_adopting")

fig, (ax, rax) = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True, gridspec_kw={{"height_ratios": [3, 1], "hspace": 0.05}})
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
residual_summaries = []
for i, pha in enumerate(source_spectra, start=1):
    color = colors[(i - 1) % len(colors)]
    label = pha.rsplit("/", 1)[-1].replace(".pi", "")
    dp = get_data_plot(i)
    mp = get_model_plot(i)
    rp = get_resid_plot(i)
    resid = np.asarray(rp.y, dtype=float)
    resid = resid[np.isfinite(resid)]
    residual_summaries.append({{
        "dataset_id": i,
        "spectrum": pha,
        "n_bins": int(resid.size),
        "mean_residual": float(np.mean(resid)) if resid.size else None,
        "rms_residual": float(np.sqrt(np.mean(resid * resid))) if resid.size else None,
        "max_abs_residual": float(np.max(np.abs(resid))) if resid.size else None,
    }})
    ax.errorbar(dp.x, dp.y, yerr=getattr(dp, "yerr", None), fmt="o", ms=3, lw=0.8, alpha=0.75, color=color, label=f"{{label}} data")
    ax.plot(mp.x, mp.y, color=color, lw=1.5, label=f"{{label}} model")
    rax.axhline(0, color="0.25", ls="--", lw=0.8)
    rax.errorbar(rp.x, rp.y, yerr=getattr(rp, "yerr", None), fmt="o", ms=3, lw=0.8, alpha=0.75, color=color)
ax.set_yscale("log")
ax.set_ylabel("Counts s$^{{-1}}$ keV$^{{-1}}$")
rax.set_xlabel("Energy (keV)")
rax.set_ylabel("Residual")
ax.set_title("Source fit with annulus-constrained XRB")
ax.text(0.02, 0.03, plot_caveat, transform=ax.transAxes, fontsize=8, bbox={{"facecolor": "white", "edgecolor": "0.7", "alpha": 0.85}})
ax.legend(fontsize=6, ncol=2)
ax.grid(alpha=0.2)
rax.grid(alpha=0.2)
fig.savefig("{out_plot}", dpi=180, bbox_inches="tight")
plt.close(fig)

out = {{
    "method": "phase3_BC_annulus_constrained_xrb",
    "xrb_policy": xrb_policy,
    "abundance_policy": abundance_policy,
    "model_annulus": "lhb + phabs*(halo + cxb + icm_ann)",
    "model_source": "lhb + phabs*(halo + cxb + icm_src)",
    "statname": fr.statname,
    "statval": float(fr.statval),
    "dof": int(fr.dof),
    "rstat": None if getattr(fr, "rstat", None) is None else float(fr.rstat),
    "q_value": None if getattr(fr, "qval", None) is None else float(fr.qval),
    "temperature_keV": float(icm_src.kT.val),
    "apec_norm": float(icm_src.norm.val),
    "abundance_solar": float(icm_src.Abundanc.val),
    "nH_1e22_cm2": float(gal_src.nH.val),
    "redshift": float(icm_src.redshift.val),
    "confidence_intervals": confidence,
    "soft_flux_unabsorbed_erg_s_cm2": soft_flux_unabs,
    "bolometric_flux_unabsorbed_erg_s_cm2": bolo_flux_unabs,
    "soft_luminosity_unabsorbed_erg_s": soft_lum,
    "bolometric_luminosity_unabsorbed_erg_s": bolo_lum,
    "fit_band_keV": [fit_band[0], fit_band[1]],
    "source_spectra": source_spectra,
    "annulus_spectra": annulus_spectra,
    "source_prefit": prefit_values,
    "annulus_fit": ann_values,
    "xrb_area_scale_source_over_annulus": {xrb_area_scale_source_over_annulus:.12g},
    "r_em_annulus_to_source": {r_em:.12g},
    "qa_flags": qa_flags,
    "plot_caveat": plot_caveat,
    "fit_plot_png": "{out_plot}",
    "residual_summaries": residual_summaries,
}}
out["n_free_parameters"] = 2
if abundance_policy == "free_source":
    out["n_free_parameters"] = 3
out["aic_wstat"] = out["statval"] + 2.0 * out["n_free_parameters"]
out["bic_wstat"] = out["statval"] + out["n_free_parameters"] * math.log(len(source_spectra) * 440.0)
out["model_selection_note"] = "For WSTAT fits compare variants with lower AIC/BIC; q_value is reported but is not the main selection criterion."
with open("{out_json}", "w") as f:
    json.dump(out, f, indent=2, sort_keys=True)
print(json.dumps(out, indent=2, sort_keys=True))
''')


def run_sherpa(script: Path, fit_dir: Path) -> None:
    """Run Sherpa in batch mode."""
    run(["sherpa", "-n", "-b", str(script)], cwd=fit_dir)


# --- Beta model loading ---
def load_beta_model(cluster_dir: Path, cluster_key: str) -> dict | None:
    """Load beta model R_EM from existing JSON."""
    candidates = []
    for key in _alt_cluster_keys(cluster_key):
        candidates.extend([
            cluster_dir / "postprocess_r500_blanksky" / f"{key}_beta_model.json",
            cluster_dir / "postprocess_r500" / f"{key}_beta_model.json",
        ])
    for p in candidates:
        if p.exists():
            with open(p) as f:
                return json.load(f)
    return None


# --- Find flux image ---
def find_flux_image(cluster_dir: Path) -> Path | None:
    """Find the merged flux image for point source detection."""
    candidates = [
        cluster_dir / "processed" / "clean_fluxed" / "flux_clean.img",
        cluster_dir / "processed" / "broad_flux.img",
        cluster_dir / "processed" / "broad_thresh.img",
    ]
    for p in candidates:
        if p.exists():
            return p
    flux_imgs = sorted(cluster_dir.glob("processed/*flux*.img"))
    return flux_imgs[0] if flux_imgs else None


# --- Find source catalog ---
def find_source_catalog(cluster_dir: Path) -> Path | None:
    """Find wavdetect source catalog."""
    candidates = [
        cluster_dir / "processed" / "src.fits",
    ]
    for p in candidates:
        if p.exists():
            return p
    srcs = sorted(cluster_dir.glob("processed/src*.fits"))
    return srcs[0] if srcs else None


def _find_cluster_dir(key: str, config: ClusterConfig) -> Path | None:
    """Find cluster directory using both naming conventions."""
    d = default_cluster_dir(key, config)
    if d is not None:
        return d
    alt = _alt_cluster_key(key)
    if alt != key:
        d = default_cluster_dir(alt, config)
        if d is not None:
            return d
    return None


# --- Main ---
def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cluster", required=True)
    p.add_argument("--cluster-table", type=Path, default=CLUSTER_TABLE_PATH)
    p.add_argument("--h0", type=float, default=DEFAULT_H0)
    p.add_argument("--omega-m", type=float, default=DEFAULT_OMEGA_M)
    p.add_argument("--xrb-policy", choices=("fixed_shape", "flexible"), default="fixed_shape")
    p.add_argument("--abundance-policy", choices=("fixed", "free_source"), default="fixed")
    p.add_argument("--fit-min-kev", type=float, default=DEFAULT_FIT_BAND[0])
    p.add_argument("--fit-max-kev", type=float, default=DEFAULT_FIT_BAND[1])
    p.add_argument("--renormalize-blanksky-pha", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--no-run-blanksky", action="store_true")
    p.add_argument("--no-run-specextract", action="store_true")
    p.add_argument("--no-run-sherpa", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    if args.fit_min_kev >= args.fit_max_kev:
        raise SystemExit("--fit-min-kev must be < --fit-max-kev")

    # Load cluster config
    configs = load_cluster_configs_from_table(args.cluster_table)
    config_key, config = resolve_cluster_config(args.cluster, configs)
    cluster_dir = _find_cluster_dir(config_key, config)
    if cluster_dir is None:
        raise SystemExit(f"No data directory for {config_key}")
    cluster_dir = cluster_dir.resolve()

    redshift = config.redshift
    m500_raw = config.m500
    if redshift is None or m500_raw is None:
        raise SystemExit(f"Need redshift and M500 for {config_key}")
    h = args.h0 / 100.0
    m500_msun = m500_raw / h if config.m500_h_inverse else m500_raw
    nh = config.nh_1e22 or 0.02

    r500_mpc = compute_r500_mpc(m500_msun, redshift, args.h0, args.omega_m)
    r500_arcsec = angular_radius_arcsec(r500_mpc, redshift, args.h0, args.omega_m)
    kt_init = 5.0 * (m500_msun / 3e14) ** (2.0 / 3.0)
    dl_cm = luminosity_distance_cm(redshift, args.h0, args.omega_m)

    print(f"[info] {config_key}: z={redshift:.4f}, R500={r500_arcsec:.1f}\", "
          f"M500={m500_msun:.2e} Msun, kT_init={kt_init:.1f} keV")

    # Output directory
    outdir = cluster_dir / "processed_joint_bxc"
    outdir.mkdir(parents=True, exist_ok=True)
    band_tag = f"{args.fit_min_kev:g}_{args.fit_max_kev:g}".replace(".", "p")
    bkg_tag = "heRenorm" if args.renormalize_blanksky_pha else "blanksky"
    fit_tag = f"phase3_BC_{args.xrb_policy}_{args.abundance_policy}_{bkg_tag}_{band_tag}keV"
    fit_dir = outdir / "fits" / fit_tag
    fit_dir.mkdir(parents=True, exist_ok=True)

    # Discover evt2 files
    evt2_list = discover_individual_evt2(cluster_dir)
    if not evt2_list:
        raise SystemExit(f"No evt2 files found in {cluster_dir}")
    evt2_by_obsid = {obsid_from_evt_path(e): e for e in evt2_list}
    print(f"[info] Found {len(evt2_by_obsid)} ObsIDs: {sorted(evt2_by_obsid.keys())}")

    # Find analysis center (X-ray peak or catalog)
    flux_image = find_flux_image(cluster_dir)
    peak = find_xray_peak_center(
        flux_image, config.center_ra, config.center_dec,
        DEFAULT_XRAY_PEAK_SEARCH_ARCSEC,
    )
    if peak:
        center_ra, center_dec, _ = peak
        print(f"[info] Center: X-ray peak ({center_ra:.5f}, {center_dec:.5f})")
    else:
        center_ra, center_dec = config.center_ra, config.center_dec
        print(f"[info] Center: catalog ({center_ra:.5f}, {center_dec:.5f})")

    # Load point source masks
    src_catalog = find_source_catalog(cluster_dir)
    masks = load_point_source_masks(
        cluster_dir=cluster_dir,
        source_file=str(src_catalog) if src_catalog else None,
        center_ra=center_ra,
        center_dec=center_dec,
        r500_arcsec=r500_arcsec,
        max_radius_r500=DEFAULT_ANNULUS_OUTER_R500,
        sigma_min=DEFAULT_POINT_SOURCE_SIGMA_MIN,
        radius_scale=DEFAULT_POINT_SOURCE_RADIUS_SCALE,
        min_radius_pix=DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX,
        skip_center_r500=DEFAULT_POINT_SOURCE_SKIP_CENTER_R500,
    )
    print(f"[info] Point source masks: {len(masks)}")

    # Load beta model R_EM
    beta = load_beta_model(cluster_dir, config_key)
    if beta:
        r_em = beta.get("R_EM_direct", beta.get("R_EM", 0.05))
        r_em = max(r_em, 0.001)
        print(f"[info] R_EM = {r_em:.4f} (from beta model)")
    else:
        print("[warn] No beta model found; using R_EM=0.05 default")
        r_em = 0.05

    # Step 1: Generate blank-sky events
    if args.no_run_blanksky:
        blank_by_obsid = load_existing_blanksky(
            evt2_by_obsid, outdir / "blanksky", cluster_dir, config_key
        )
    else:
        blank_by_obsid = run_blanksky_for_obsids(evt2_by_obsid, outdir / "blanksky")
    print(f"[info] Blank-sky files: {len(blank_by_obsid)}/{len(evt2_by_obsid)}")

    if not blank_by_obsid:
        raise SystemExit("No blank-sky files available; cannot proceed")

    # Step 2: Extract spectra
    spectrum_sets = extract_joint_spectra(
        cluster_dir, outdir, config_key, evt2_by_obsid, blank_by_obsid,
        center_ra, center_dec, r500_arcsec, masks,
        run_specextract=not args.no_run_specextract,
    )

    # Step 3: Renormalize blank-sky backgrounds
    renorm_diagnostics: list[BackgroundRenormDiagnostic] = []
    if args.renormalize_blanksky_pha:
        spectrum_sets, renorm_diagnostics = renormalize_blanksky_background_phas(
            spectrum_sets,
            outdir / "spectra_high_energy_renorm",
            DEFAULT_BLANKSKY_RENORM_BAND,
        )
    source_spectra = [s.source_pi for s in spectrum_sets if s.source_pi]
    annulus_spectra = [s.annulus_pi for s in spectrum_sets if s.annulus_pi]
    print(f"[info] Source spectra: {len(source_spectra)}, Annulus spectra: {len(annulus_spectra)}")

    if not source_spectra:
        raise SystemExit("No source spectra available")

    # Compute area scaling
    source_area = approximate_unmasked_area_arcsec2(0.0, DEFAULT_SOURCE_OUTER_R500, r500_arcsec, masks)
    annulus_area = approximate_unmasked_area_arcsec2(
        DEFAULT_ANNULUS_INNER_R500, DEFAULT_ANNULUS_OUTER_R500, r500_arcsec, masks
    )
    area_scale = source_area / annulus_area

    # Step 4: Sherpa fit
    if not args.no_run_sherpa and annulus_spectra:
        sherpa_script = fit_dir / f"fit_{config_key}_{fit_tag}_sherpa.py"
        fit_json = fit_dir / f"{config_key}_{fit_tag}_fit_results.json"
        fit_plot = fit_dir / f"{config_key}_{fit_tag}_fit_plot.png"

        write_joint_sherpa_script(
            sherpa_script, fit_json, fit_plot,
            [str(p) for p in source_spectra],
            [str(p) for p in annulus_spectra],
            redshift, nh, dl_cm, kt_init,
            r_em, area_scale, args.xrb_policy,
            (args.fit_min_kev, args.fit_max_kev),
            args.abundance_policy,
        )
        print(f"[info] Running Sherpa fit...")
        run_sherpa(sherpa_script, fit_dir)
    elif not args.no_run_sherpa and not annulus_spectra:
        print("[warn] No annulus spectra; skipping joint fit")
        fit_json = None
        fit_plot = None
    else:
        fit_json = None
        fit_plot = None

    # Read and display results
    fit_result = None
    if fit_json and Path(fit_json).exists():
        with open(fit_json) as f:
            fit_result = json.load(f)
        tx = fit_result.get("temperature_keV", "N/A")
        rstat = fit_result.get("rstat", "N/A")
        lx = fit_result.get("bolometric_luminosity_unabsorbed_erg_s", "N/A")
        print(f"\n{'='*50}")
        print(f"  {config_key}: T_X = {tx:.2f} keV" if isinstance(tx, float) else f"  T_X = {tx}")
        print(f"  rstat = {rstat:.3f}" if isinstance(rstat, float) else f"  rstat = {rstat}")
        if isinstance(lx, float):
            print(f"  L_X (bol) = {lx:.2e} erg/s")
        print(f"{'='*50}")

    # Copy outputs to output/ directory
    output_figs = Path("output/figures/spectral")
    output_prods = Path("output/products/spectral")
    output_figs.mkdir(parents=True, exist_ok=True)
    output_prods.mkdir(parents=True, exist_ok=True)

    if fit_plot and Path(fit_plot).exists():
        shutil.copy2(fit_plot, output_figs / f"{config_key}_fit.png")
    if fit_result:
        with open(output_prods / f"{config_key}_results.json", "w") as f:
            json.dump(fit_result, f, indent=2, sort_keys=True)

    # Write summary JSON
    summary = {
        "cluster_key": config_key,
        "redshift": redshift,
        "m500_msun": m500_msun,
        "r500_arcsec": r500_arcsec,
        "r500_mpc": r500_mpc,
        "nH_1e22": nh,
        "kt_init": kt_init,
        "fit_tag": fit_tag,
        "xrb_policy": args.xrb_policy,
        "abundance_policy": args.abundance_policy,
        "blanksky_pha_high_energy_renormalized": args.renormalize_blanksky_pha,
        "blanksky_renorm_band_keV": list(DEFAULT_BLANKSKY_RENORM_BAND),
        "blanksky_renorm_diagnostics": [asdict(d) for d in renorm_diagnostics],
        "fit_band_keV": [args.fit_min_kev, args.fit_max_kev],
        "r_em_annulus_to_source": r_em,
        "xrb_area_scale_source_over_annulus": area_scale,
        "n_obsids": len(evt2_by_obsid),
        "n_blanksky": len(blank_by_obsid),
        "n_source_spectra": len(source_spectra),
        "n_annulus_spectra": len(annulus_spectra),
        "fit_result": fit_result,
    }
    summary_path = outdir / "results" / f"{config_key}_{fit_tag}_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"\n[info] Summary: {summary_path}")
    print(f"[info] Fit plot: {output_figs / f'{config_key}_fit.png'}")


if __name__ == "__main__":
    main()
