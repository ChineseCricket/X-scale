#!/usr/bin/env python3
"""Source+annulus blank-sky/XRB joint spectral pipeline.

This implements the Phase-3 B+C plan:
1. Fit a beta model to the merged flux-image surface-brightness profile.
2. Extract per-ObsID source and outer-annulus spectra, both with CIAO blank-sky
   background PHAs. No merged spectra are used.
3. Fit annulus spectra first with LHB + absorbed(halo + CXB + ICM_ann).
4. Freeze/area-scale the fitted XRB components into the source fit and measure
   ICM source temperature/luminosity.

The defaults run Abell_383 from the current project tree. Edit constants below
for batch work, or use the optional CLI overrides.
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

PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from beta_model_profile import run_beta_profile  # noqa: E402
from complete_xray_pipeline import (  # noqa: E402
    DEFAULT_ABUNDANCE,
    DEFAULT_BANDS,
    DEFAULT_DISPLAY_SMOOTH_SIGMA_PIX,
    DEFAULT_H0,
    DEFAULT_NH_1E22,
    DEFAULT_OMEGA_M,
    DEFAULT_XRAY_PEAK_SEARCH_ARCSEC,
    choose_image,
    make_smoothed_display_image,
    read_cluster_table,
    reprocess_obsids,
    run_blanksky_for_obsids,
    run_merge_obs,
    run_wavdetect,
)
from postprocess_cluster import (  # noqa: E402
    DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX,
    DEFAULT_POINT_SOURCE_RADIUS_SCALE,
    DEFAULT_POINT_SOURCE_SIGMA_MIN,
    DEFAULT_POINT_SOURCE_SKIP_CENTER_R500,
    angular_radius_arcsec,
    compute_r500_mpc,
    find_xray_peak_center,
    load_point_source_masks,
    luminosity_distance_cm,
    source_masks_for_event,
    sky_xy_from_event_wcs,
    write_aperture_overlay_plot,
)

DEFAULT_CLUSTER_KEY = "Abell_383"
DEFAULT_CLUSTER_DIR = PROJECT_DIR / "chandra_data" / "Abell_383"
DEFAULT_CLUSTER_TABLE = PROJECT_DIR / "cluster_center_table.csv"
DEFAULT_OUTPUT_DIRNAME = "processed_joint_bxc"
DEFAULT_FIT_BAND = (0.5, 7.0)
DEFAULT_SOURCE_INNER_R500 = 0.0
DEFAULT_SOURCE_OUTER_R500 = 1.0
DEFAULT_ANNULUS_INNER_R500 = 1.2
DEFAULT_ANNULUS_OUTER_R500 = 1.8
DEFAULT_PROFILE_NBINS = 20
DEFAULT_PROFILE_MAX_R500 = 2.0
DEFAULT_LHB_KT = 0.10
DEFAULT_LHB_NORM = 5.0e-6
DEFAULT_HALO_KT = 0.25
DEFAULT_HALO_NORM_INIT = 1.0e-6
DEFAULT_CXB_INDEX = 1.40
DEFAULT_CXB_NORM_INIT = 1.0e-5
DEFAULT_ICM_ANN_KT_FACTOR = 0.7
DEFAULT_SPECEXTRACT_WEIGHT = "no"
DEFAULT_SPECEXTRACT_BKGRESP = "no"
DEFAULT_XRB_POLICY = "fixed_shape"
DEFAULT_ABUNDANCE_POLICY = "fixed"
DEFAULT_BLANKSKY_RENORM_BAND = (9.5, 12.0)


@dataclass
class SpectrumSet:
    obsid: str
    source_pi: str | None
    annulus_pi: str | None
    source_region: str
    annulus_region: str
    evt_file: str
    blanksky_file: str


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


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+ " + " ".join(str(c) for c in cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def load_existing_blanksky(evt2_by_obsid: dict[str, Path], outdir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for obsid in evt2_by_obsid:
        p = outdir / f"obs{obsid}_blanksky_evt.fits"
        if p.exists():
            out[obsid] = p.resolve()
    return out


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


def run_specextract_blanksky(cluster_dir: Path, evt: Path, blank_evt: Path, region: Path, outroot: Path) -> Path | None:
    if shutil.which("specextract") is None:
        print("[warn] specextract not found; skipping extraction")
        return None
    cmd = [
        "specextract",
        f"infile={evt}[sky=region({region})]",
        f"bkgfile={blank_evt}[sky=region({region})]",
        f"outroot={outroot}",
        "correctpsf=no",
        f"weight={DEFAULT_SPECEXTRACT_WEIGHT}",
        f"bkgresp={DEFAULT_SPECEXTRACT_BKGRESP}",
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


def approximate_unmasked_area_arcsec2(inner_r500: float, outer_r500: float, r500_arcsec: float, masks: list[Any]) -> float:
    area = math.pi * ((outer_r500 * r500_arcsec) ** 2 - (inner_r500 * r500_arcsec) ** 2)
    for src in masks:
        sep = getattr(src, "separation_arcsec", None)
        rad = getattr(src, "radius_arcsec", 0.0)
        if sep is not None and inner_r500 * r500_arcsec <= sep <= outer_r500 * r500_arcsec:
            area -= math.pi * rad * rad
    return max(area, 1.0)


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
) -> list[SpectrumSet]:
    spectra_dir = outdir / "spectra"
    region_dir = outdir / "regions" / "per_obs"
    products: list[SpectrumSet] = []
    for obsid, evt in evt2_by_obsid.items():
        if obsid not in blank_by_obsid:
            print(f"[warn] no blank-sky file for ObsID {obsid}; skipping this ObsID")
            continue
        blank = blank_by_obsid[obsid]
        src_reg = write_event_region(region_dir / f"{cluster_key}_obs{obsid}_src_r500.reg", evt, center_ra, center_dec, r500_arcsec, DEFAULT_SOURCE_INNER_R500, DEFAULT_SOURCE_OUTER_R500, masks)
        ann_reg = write_event_region(region_dir / f"{cluster_key}_obs{obsid}_ann_{DEFAULT_ANNULUS_INNER_R500:.1f}_{DEFAULT_ANNULUS_OUTER_R500:.1f}r500.reg", evt, center_ra, center_dec, r500_arcsec, DEFAULT_ANNULUS_INNER_R500, DEFAULT_ANNULUS_OUTER_R500, masks)
        src_pi = spectra_dir / f"{cluster_key}_obs{obsid}_src_r500.pi"
        ann_pi = spectra_dir / f"{cluster_key}_obs{obsid}_ann_{DEFAULT_ANNULUS_INNER_R500:.1f}_{DEFAULT_ANNULUS_OUTER_R500:.1f}r500.pi"
        if run_specextract:
            src = run_specextract_blanksky(cluster_dir, evt, blank, src_reg, spectra_dir / f"{cluster_key}_obs{obsid}_src_r500")
            ann = run_specextract_blanksky(cluster_dir, evt, blank, ann_reg, spectra_dir / f"{cluster_key}_obs{obsid}_ann_{DEFAULT_ANNULUS_INNER_R500:.1f}_{DEFAULT_ANNULUS_OUTER_R500:.1f}r500")
        else:
            src = src_pi.resolve() if src_pi.exists() else None
            ann = ann_pi.resolve() if ann_pi.exists() else None
        products.append(SpectrumSet(obsid, str(src) if src else None, str(ann) if ann else None, str(src_reg), str(ann_reg), str(evt), str(blank)))
    return products


def _pha_high_energy_renorm_factor(src_pi: Path, bkg_pi: Path, rmf: Path, band: tuple[float, float]) -> dict[str, float]:
    from astropy.io import fits
    import numpy as np

    with fits.open(src_pi) as hs, fits.open(bkg_pi) as hb, fits.open(rmf) as hr:
        sdat = hs[1].data
        bdat = hb[1].data
        ebounds = hr["EBOUNDS"].data
        ebounds_by_channel = {
            int(channel): (float(e_min), float(e_max))
            for channel, e_min, e_max in zip(ebounds["CHANNEL"], ebounds["E_MIN"], ebounds["E_MAX"])
        }
        energy_mid = np.array(
            [
                0.5 * (ebounds_by_channel[int(channel)][0] + ebounds_by_channel[int(channel)][1])
                for channel in sdat["CHANNEL"]
            ]
        )
        keep = (energy_mid >= band[0]) & (energy_mid <= band[1])
        source_counts = float(np.asarray(sdat["COUNTS"])[keep].sum())
        background_counts = float(np.asarray(bdat["COUNTS"])[keep].sum())
        src_exposure = float(hs[1].header.get("EXPOSURE", 1.0))
        bkg_exposure = float(hb[1].header.get("EXPOSURE", 1.0))
        src_backscal = float(hs[1].header.get("BACKSCAL", 1.0))
        bkg_backscal = float(hb[1].header.get("BACKSCAL", 1.0))
        src_areascale = float(hs[1].header.get("AREASCAL", 1.0))
        bkg_areascale = float(hb[1].header.get("AREASCAL", 1.0))

    # Sherpa/XSPEC background scaling uses exposure, BACKSCAL, and AREASCAL.
    # CIAO blank-sky science products are commonly checked/rescaled in a
    # particle-dominated hard band. Reducing the background AREASCAL increases
    # the background contribution by the same factor.
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
    """Copy spectra and renormalize blank-sky background PHAs in 9.5-12 keV.

    This follows the usual CIAO blank-sky validation step: the cluster should
    contribute negligibly above about 9.5 keV, so a mismatch there is primarily
    the particle background normalization. We write copies instead of mutating
    the original specextract products.
    """
    from astropy.io import fits
    import shutil as _shutil

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
            _shutil.copy2(src_pi, new_src)
            _shutil.copy2(bkg_pi, new_bkg)
            _shutil.copy2(arf, new_arf)
            _shutil.copy2(rmf, new_rmf)
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
            diagnostics.append(
                BackgroundRenormDiagnostic(
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
                )
            )
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
# This gives the beta model an actual source normalization to project into the
# annulus, rather than leaving the annulus ICM normalization fully degenerate
# with the sky background components.
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

# Step 2b: source fit freezes XRB shape and annulus-derived normalization,
# scaled by geometric extraction area. The cluster ICM is the science component.
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
    run(["sherpa", "-n", "-b", str(script)], cwd=fit_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster-key", default=DEFAULT_CLUSTER_KEY)
    parser.add_argument("--cluster-dir", type=Path, default=DEFAULT_CLUSTER_DIR)
    parser.add_argument("--cluster-table", type=Path, default=DEFAULT_CLUSTER_TABLE)
    parser.add_argument("--output-dirname", default=DEFAULT_OUTPUT_DIRNAME)
    parser.add_argument("--fit-min-kev", type=float, default=DEFAULT_FIT_BAND[0])
    parser.add_argument("--fit-max-kev", type=float, default=DEFAULT_FIT_BAND[1])
    parser.add_argument("--no-run-repro", action="store_true")
    parser.add_argument("--no-run-imaging", action="store_true")
    parser.add_argument("--no-run-blanksky", action="store_true")
    parser.add_argument("--no-run-specextract", action="store_true")
    parser.add_argument("--no-run-sherpa", action="store_true")
    parser.add_argument("--xrb-policy", choices=("fixed_shape", "flexible"), default=DEFAULT_XRB_POLICY)
    parser.add_argument("--abundance-policy", choices=("fixed", "free_source"), default=DEFAULT_ABUNDANCE_POLICY)
    parser.add_argument("--renormalize-blanksky-pha", action="store_true")
    args = parser.parse_args()
    if args.fit_min_kev >= args.fit_max_kev:
        raise SystemExit("--fit-min-kev must be smaller than --fit-max-kev")

    row = read_cluster_table(args.cluster_table, args.cluster_key)
    cluster_dir = args.cluster_dir.resolve()
    outdir = cluster_dir / args.output_dirname
    outdir.mkdir(parents=True, exist_ok=True)
    results_dir = outdir / "results"
    figures_dir = outdir / "figures"
    band_tag = f"{args.fit_min_kev:g}_{args.fit_max_kev:g}".replace(".", "p")
    bkg_tag = "heRenorm" if args.renormalize_blanksky_pha else "blanksky"
    fit_tag = f"phase3_BC_{args.xrb_policy}_{args.abundance_policy}_{bkg_tag}_{band_tag}keV"
    fit_dir = outdir / "fits" / fit_tag
    for d in (results_dir, figures_dir, fit_dir):
        d.mkdir(parents=True, exist_ok=True)

    r500_mpc = compute_r500_mpc(row.m500_msun, row.z, DEFAULT_H0, DEFAULT_OMEGA_M)
    r500_arcsec = angular_radius_arcsec(r500_mpc, row.z, DEFAULT_H0, DEFAULT_OMEGA_M)
    kt_init = 5.0 * (row.m500_msun / 3e14) ** (2.0 / 3.0)

    evt2_by_obsid = reprocess_obsids(cluster_dir, row.obsids, not args.no_run_repro)
    imaging_info = run_merge_obs(list(evt2_by_obsid.values()), outdir / "imaging", bands=DEFAULT_BANDS) if not args.no_run_imaging else {"products": []}
    img_for_sources = choose_image(outdir / "imaging", "thresh") or choose_image(outdir / "imaging", "flux")
    if img_for_sources is None:
        raise SystemExit("No merged image found")
    img_for_display_raw = choose_image(outdir / "imaging", "flux") or img_for_sources
    img_for_display = make_smoothed_display_image(img_for_display_raw, outdir / "imaging", sigma_pix=DEFAULT_DISPLAY_SMOOTH_SIGMA_PIX)
    src_fits = run_wavdetect(img_for_sources, outdir / "imaging")

    peak = find_xray_peak_center(img_for_display, row.ra, row.dec, DEFAULT_XRAY_PEAK_SEARCH_ARCSEC)
    if peak is None:
        center_ra, center_dec, center_offset = row.ra, row.dec, 0.0
        center_mode = "catalog"
    else:
        center_ra, center_dec, center_offset = peak
        center_mode = "xray_peak"

    masks = load_point_source_masks(
        cluster_dir=cluster_dir,
        source_file=str(src_fits.relative_to(cluster_dir)),
        center_ra=center_ra,
        center_dec=center_dec,
        r500_arcsec=r500_arcsec,
        max_radius_r500=DEFAULT_ANNULUS_OUTER_R500,
        sigma_min=DEFAULT_POINT_SOURCE_SIGMA_MIN,
        radius_scale=DEFAULT_POINT_SOURCE_RADIUS_SCALE,
        min_radius_pix=DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX,
        skip_center_r500=DEFAULT_POINT_SOURCE_SKIP_CENTER_R500,
    )

    beta = run_beta_profile(
        img_for_display,
        center_ra,
        center_dec,
        r500_arcsec,
        results_dir / f"{row.key}_beta_profile.json",
        figures_dir / f"{row.key}_beta_profile.png",
        nbins=DEFAULT_PROFILE_NBINS,
        max_radius_r500=DEFAULT_PROFILE_MAX_R500,
        source_inner_r500=DEFAULT_SOURCE_INNER_R500,
        source_outer_r500=DEFAULT_SOURCE_OUTER_R500,
        annulus_inner_r500=DEFAULT_ANNULUS_INNER_R500,
        annulus_outer_r500=DEFAULT_ANNULUS_OUTER_R500,
    )

    if args.no_run_blanksky:
        blank_by_obsid = load_existing_blanksky(evt2_by_obsid, outdir / "blanksky")
    else:
        blank_by_obsid = run_blanksky_for_obsids(evt2_by_obsid, cluster_dir, outdir / "blanksky", require=False)

    spectrum_sets = extract_joint_spectra(
        cluster_dir,
        outdir,
        row.key,
        evt2_by_obsid,
        blank_by_obsid,
        center_ra,
        center_dec,
        r500_arcsec,
        masks,
        run_specextract=not args.no_run_specextract,
    )
    renorm_diagnostics: list[BackgroundRenormDiagnostic] = []
    if args.renormalize_blanksky_pha:
        spectrum_sets, renorm_diagnostics = renormalize_blanksky_background_phas(
            spectrum_sets,
            outdir / "spectra_high_energy_renorm",
            DEFAULT_BLANKSKY_RENORM_BAND,
        )
    source_spectra = [s.source_pi for s in spectrum_sets if s.source_pi]
    annulus_spectra = [s.annulus_pi for s in spectrum_sets if s.annulus_pi]

    source_area = approximate_unmasked_area_arcsec2(DEFAULT_SOURCE_INNER_R500, DEFAULT_SOURCE_OUTER_R500, r500_arcsec, masks)
    annulus_area = approximate_unmasked_area_arcsec2(DEFAULT_ANNULUS_INNER_R500, DEFAULT_ANNULUS_OUTER_R500, r500_arcsec, masks)
    area_scale = source_area / annulus_area

    aperture_plot = write_aperture_overlay_plot(
        img_for_display,
        figures_dir / f"{row.key}_phase3_source_aperture.png",
        center_ra,
        center_dec,
        r500_arcsec,
        DEFAULT_ANNULUS_INNER_R500,
        DEFAULT_ANNULUS_OUTER_R500,
        DEFAULT_SOURCE_INNER_R500,
        masks,
        f"{row.key} Phase-3 source/annulus apertures",
        source_outer_r500=DEFAULT_SOURCE_OUTER_R500,
    )

    sherpa_script = fit_json = fit_plot = None
    if source_spectra and annulus_spectra and not args.no_run_sherpa:
        sherpa_script = fit_dir / f"fit_{row.key}_{fit_tag}_sherpa.py"
        fit_json = fit_dir / f"{row.key}_{fit_tag}_fit_results.json"
        fit_plot = fit_dir / f"{row.key}_{fit_tag}_fit_plot.png"
        write_joint_sherpa_script(
            sherpa_script,
            fit_json,
            fit_plot,
            [str(p) for p in source_spectra],
            [str(p) for p in annulus_spectra],
            row.z,
            getattr(row, "nh_1e22", DEFAULT_NH_1E22),
            luminosity_distance_cm(row.z, DEFAULT_H0, DEFAULT_OMEGA_M),
            kt_init,
            beta.r_em_annulus_to_source,
            area_scale,
            args.xrb_policy,
            (args.fit_min_kev, args.fit_max_kev),
            args.abundance_policy,
        )
        run_sherpa(sherpa_script, fit_dir)

    fit_result = json.loads(Path(fit_json).read_text()) if fit_json and Path(fit_json).exists() else None
    summary = {
        "cluster": asdict(row),
        "cluster_dir": str(cluster_dir),
        "output_dir": str(outdir),
        "method": "phase3_BC_surface_brightness_constrained_source_plus_background",
        "xrb_policy": args.xrb_policy,
        "abundance_policy": args.abundance_policy,
        "blanksky_pha_high_energy_renormalized": args.renormalize_blanksky_pha,
        "blanksky_renorm_band_keV": list(DEFAULT_BLANKSKY_RENORM_BAND),
        "blanksky_renorm_diagnostics": [asdict(d) for d in renorm_diagnostics],
        "fit_band_keV": [args.fit_min_kev, args.fit_max_kev],
        "fit_tag": fit_tag,
        "r500_mpc": r500_mpc,
        "r500_arcsec": r500_arcsec,
        "center_mode": center_mode,
        "fit_center_ra_deg": center_ra,
        "fit_center_dec_deg": center_dec,
        "center_offset_from_catalog_arcsec": center_offset,
        "evt2_by_obsid": {k: str(v) for k, v in evt2_by_obsid.items()},
        "blanksky_by_obsid": {k: str(v) for k, v in blank_by_obsid.items()},
        "imaging": imaging_info,
        "source_catalog": str(src_fits),
        "display_image": str(img_for_display),
        "point_source_mask_count": len(masks),
        "beta_profile_json": str(results_dir / f"{row.key}_beta_profile.json"),
        "beta_profile_plot": str(figures_dir / f"{row.key}_beta_profile.png"),
        "r_em_annulus_to_source": beta.r_em_annulus_to_source,
        "xrb_area_scale_source_over_annulus": area_scale,
        "source_area_arcsec2_approx": source_area,
        "annulus_area_arcsec2_approx": annulus_area,
        "aperture_plot": str(aperture_plot) if aperture_plot else None,
        "spectrum_sets": [asdict(s) for s in spectrum_sets],
        "sherpa_script": str(sherpa_script) if sherpa_script else None,
        "fit_json": str(fit_json) if fit_json else None,
        "fit_plot": str(fit_plot) if fit_plot else None,
        "fit_result": fit_result,
    }
    summary_path = results_dir / f"{row.key}_{fit_tag}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("\nWrote summary:", summary_path)


if __name__ == "__main__":
    main()
