#!/usr/bin/env python3
"""Complete CIAO/Sherpa X-ray pipeline for cluster scaling-relation products.

Default target: Abell_383 raw Chandra data. The pipeline follows the CIAO-first
workflow: reprocess each ObsID, create merged imaging products, detect point
sources, make blank-sky backgrounds, extract per-ObsID spectra, and jointly fit
those spectra in Sherpa. Merged products are never used for spectral fitting.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from postprocess_cluster import (
    DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX,
    DEFAULT_POINT_SOURCE_RADIUS_SCALE,
    DEFAULT_POINT_SOURCE_SIGMA_MIN,
    DEFAULT_POINT_SOURCE_SKIP_CENTER_R500,
    PointSourceMask,
    angular_radius_arcsec,
    apply_region_exclusions,
    compute_r500_mpc,
    count_events_in_xy_annulus,
    find_xray_peak_center,
    load_point_source_masks,
    luminosity_distance_cm,
    sky_xy_from_event_wcs,
    source_masks_for_event,
    write_aperture_overlay_plot,
    write_region,
)

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CLUSTER_KEY = "Abell_383"
DEFAULT_CLUSTER_DIR = PROJECT_DIR / "chandra_data" / "Abell_383"
DEFAULT_CLUSTER_TABLE = PROJECT_DIR / "cluster_center_table.csv"
DEFAULT_OUTPUT_DIRNAME = "processed_pipeline"
DEFAULT_BACKGROUND_MODE = "paper_hybrid"
DEFAULT_FIT_STAT = "wstat"
DEFAULT_FIT_BAND = (0.7, 7.0)
DEFAULT_SOFT_REST_BAND = (0.5, 2.0)
DEFAULT_BOLO_REST_BAND = (0.01, 100.0)
DEFAULT_CORE_INNER_R500 = 0.15
DEFAULT_XRAY_PEAK_SEARCH_ARCSEC = 120.0
DEFAULT_H0 = 70.0
DEFAULT_OMEGA_M = 0.3
DEFAULT_NH_1E22 = 0.0412
DEFAULT_ABUNDANCE = 0.3
DEFAULT_BANDS = "0.5:2.0:1.0"
DEFAULT_SPECEEXTRACT_WEIGHT = False
DEFAULT_DISPLAY_SMOOTH_SIGMA_PIX = 4.0
DEFAULT_LOCAL_BKG_EXCLUDE_R500 = 1.2


@dataclass
class ClusterRow:
    key: str
    name: str
    ra: float
    dec: float
    z: float
    m500_msun: float
    obsids: list[str]
    nh_1e22: float = DEFAULT_NH_1E22


@dataclass
class PipelineConfig:
    cluster_key: str
    cluster_dir: Path
    cluster_table: Path
    output_dir: Path
    h0: float
    omega_m: float
    fit_band: tuple[float, float]
    soft_rest_band: tuple[float, float]
    bolo_rest_band: tuple[float, float]
    xray_peak_search_arcsec: float
    require_blanksky: bool
    run_repro: bool
    run_imaging: bool
    run_blanksky: bool
    run_specextract: bool
    run_sherpa: bool


@dataclass
class ApertureProduct:
    label: str
    source_inner_r500: float
    source_outer_r500: float
    spectra: list[str]
    sherpa_script: str | None
    fit_json: str | None
    fit_plot: str | None
    aperture_plot: str | None
    source_region: str | None
    background_by_obsid: dict[str, Any] | None


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+ " + " ".join(str(c) for c in cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def read_cluster_table(path: Path, key: str) -> ClusterRow:
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["cluster_key"] == key:
                m500 = float(row.get("m500_physical_msun_h70") or row["m500_input"])
                obsids = [x.strip() for x in row["obsids"].split(";") if x.strip()]
                return ClusterRow(
                    key=key,
                    name=row["cluster_name"],
                    ra=float(row["ra_deg"]),
                    dec=float(row["dec_deg"]),
                    z=float(row["redshift"]),
                    m500_msun=m500,
                    obsids=obsids,
                )
    raise SystemExit(f"Cluster key {key!r} not found in {path}")


def find_one(patterns: list[str], base: Path) -> Path | None:
    for pattern in patterns:
        found = sorted(base.glob(pattern))
        if found:
            return found[0]
    return None


def find_many(patterns: list[str], base: Path) -> list[Path]:
    out: list[Path] = []
    for pattern in patterns:
        out.extend(sorted(base.glob(pattern)))
    return out


def reprocess_obsids(cluster_dir: Path, obsids: list[str], run_repro: bool) -> dict[str, Path]:
    evt2_by_obsid: dict[str, Path] = {}
    for obsid in obsids:
        obs_dir = cluster_dir / "raw" / obsid
        repro_dir = obs_dir / "repro"
        existing = find_one(["*repro_evt2.fits", "*repro_evt2.fits.gz"], repro_dir)
        if run_repro and existing is None:
            run(["chandra_repro", f"indir={obs_dir}", f"outdir={repro_dir}", "check_vf_pha=yes", "clobber=yes", "mode=h"])
            existing = find_one(["*repro_evt2.fits", "*repro_evt2.fits.gz"], repro_dir)
        if existing is None:
            existing = find_one(["primary/*evt2.fits", "primary/*evt2.fits.gz"], obs_dir)
        if existing is None:
            raise SystemExit(f"No evt2 found for ObsID {obsid} after reprocessing check")
        evt2_by_obsid[obsid] = existing.resolve()
    return evt2_by_obsid


def find_asol_files(cluster_dir: Path, obsid: str) -> list[Path]:
    obs_dir = cluster_dir / "raw" / obsid
    files = find_many(["primary/*asol*.fits*", "secondary/**/*asol*.fits*", "repro/*asol*.fits*"], obs_dir)
    return [p.resolve() for p in files]


def run_merge_obs(evt2_paths: list[Path], outdir: Path, bands: str = DEFAULT_BANDS) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    list_file = outdir / "evt2_for_merge.lis"
    list_file.write_text("\n".join(str(p) for p in evt2_paths) + "\n")
    outroot = outdir / "merged"
    if not sorted(outdir.glob("merged*flux*.img")):
        run(["merge_obs", f"infiles=@{list_file}", f"outroot={outroot}", f"bands={bands}", "binsize=1", "clobber=yes", "mode=h"])
    images = sorted(outdir.glob("merged*"))
    return {"evt_list": str(list_file), "outroot": str(outroot), "products": [str(p) for p in images]}


def choose_image(outdir: Path, keyword: str) -> Path | None:
    candidates = sorted(outdir.glob(f"merged*{keyword}*.img")) + sorted(outdir.glob(f"*{keyword}*.img"))
    return candidates[0] if candidates else None


def make_smoothed_display_image(image: Path, outdir: Path, sigma_pix: float = DEFAULT_DISPLAY_SMOOTH_SIGMA_PIX) -> Path:
    """Create a lightly smoothed copy of the merged flux image for plotting only."""
    if sigma_pix <= 0:
        return image
    out = outdir / f"{image.stem}_display_smooth.img"
    if out.exists():
        return out
    try:
        from astropy.io import fits
    except Exception:
        print("[warn] astropy smoothing unavailable; using unsmoothed display image.")
        return image

    def gaussian_filter_numpy(arr: np.ndarray, sigma: float) -> np.ndarray:
        radius = max(1, int(math.ceil(4.0 * sigma)))
        x = np.arange(-radius, radius + 1, dtype=float)
        kernel = np.exp(-0.5 * (x / sigma) ** 2)
        kernel /= kernel.sum()
        tmp = np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="same"), 1, arr)
        return np.apply_along_axis(lambda m: np.convolve(m, kernel, mode="same"), 0, tmp)

    with fits.open(image) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        data = np.asarray(hdu.data, dtype=float)
        valid = np.isfinite(data)
        work = np.where(valid, data, 0.0)
        weight = gaussian_filter_numpy(valid.astype(float), sigma_pix)
        smooth = gaussian_filter_numpy(work, sigma_pix)
        with np.errstate(invalid="ignore", divide="ignore"):
            smooth = np.where(weight > 0, smooth / weight, np.nan)
        hdu.data = smooth.astype("float32")
        hdu.header["HISTORY"] = f"Display-only Gaussian smoothing, sigma={sigma_pix} pixels"
        hdul.writeto(out, overwrite=True)
    return out


def run_wavdetect(image: Path, outdir: Path) -> Path:
    src = outdir / "src.fits"
    if not src.exists():
        run([
            "wavdetect",
            f"infile={image}",
            f"outfile={src}",
            f"scellfile={outdir / 'scell.fits'}",
            f"imagefile={outdir / 'imgfile.fits'}",
            f"defnbkgfile={outdir / 'nbkg.fits'}",
            "scales=2.0 4.0 8.0 16.0",
            "clobber=yes",
            "mode=h",
        ])
    return src


def run_csmooth(image: Path, outdir: Path) -> Path:
    smoothed = outdir / "merged_csmooth.img"
    if not smoothed.exists():
        run(["csmooth", f"infile={image}", f"outfile={smoothed}", "sigmin=2", "sigmax=5", "clobber=yes", "mode=h"])
    return smoothed


def run_blanksky_for_obsids(evt2_by_obsid: dict[str, Path], cluster_dir: Path, outdir: Path, require: bool) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    blank_by_obsid: dict[str, Path] = {}
    for obsid, evt in evt2_by_obsid.items():
        blank = outdir / f"obs{obsid}_blanksky_evt.fits"
        if not blank.exists():
            cmd = ["blanksky", f"evtfile={evt}", f"outfile={blank}", "weight_method=particle", "bkgparams=default", "clobber=yes", "mode=h"]
            try:
                run(cmd)
            except subprocess.CalledProcessError as exc:
                message = (
                    f"blanksky failed for ObsID {obsid}. Install/enable ACIS blank-sky CALDB files "
                    "or rerun with a different background policy."
                )
                if require:
                    raise SystemExit(message) from exc
                print("[warn]", message)
                continue
        blank_by_obsid[obsid] = blank.resolve()
    return blank_by_obsid


def event_detnam(evt: Path) -> str:
    from astropy.io import fits

    with fits.open(evt) as hdul:
        return str(hdul["EVENTS"].header.get("DETNAM", "")).strip()


def use_blanksky_for_obsid(evt: Path, mode: str = DEFAULT_BACKGROUND_MODE) -> bool:
    """Return whether this ObsID should use blank-sky background."""
    if mode == "blanksky":
        return True
    if mode == "local":
        return False
    if mode != "paper_hybrid":
        raise ValueError(f"Unknown background mode: {mode}")
    # Morandi et al. used local background for ACIS-I and blank-sky for ACIS-S.
    # In this dataset the ACIS-S observation includes chip 7.
    return "7" in event_detnam(evt)


def load_existing_blanksky_for_obsids(evt2_by_obsid: dict[str, Path], outdir: Path) -> dict[str, Path]:
    """Load previously generated blank-sky files without rerunning CIAO blanksky."""
    blank_by_obsid: dict[str, Path] = {}
    for obsid in evt2_by_obsid:
        blank = outdir / f"obs{obsid}_blanksky_evt.fits"
        if blank.exists():
            blank_by_obsid[obsid] = blank.resolve()
    return blank_by_obsid


def aperture_region_for_event(evt: Path, center_ra: float, center_dec: float, r500_arcsec: float, inner_r500: float, masks: list[PointSourceMask]) -> str:
    x, y, pix_arcsec = sky_xy_from_event_wcs(evt, center_ra, center_dec)
    r_outer = r500_arcsec / pix_arcsec
    if inner_r500 > 0:
        region = f"annulus({x:.6f},{y:.6f},{inner_r500 * r_outer:.6f},{r_outer:.6f})"
    else:
        region = f"circle({x:.6f},{y:.6f},{r_outer:.6f})"
    return apply_region_exclusions(region, source_masks_for_event(evt, masks))


def write_aperture_region_for_event(
    path: Path,
    evt: Path,
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    inner_r500: float,
    outer_r500: float,
    masks: list[PointSourceMask],
) -> Path:
    """Write a CIAO physical-coordinate aperture region for one ObsID.

    ``specextract`` is happier with a small region file than with a very long
    inline expression, especially after adding many point-source exclusions.
    The blank-sky event has already been reprojected by CIAO ``blanksky``, so
    the same physical sky region is valid for both source and background PHAs.
    """
    x, y, pix_arcsec = sky_xy_from_event_wcs(evt, center_ra, center_dec)
    r_outer = outer_r500 * r500_arcsec / pix_arcsec
    exclude_circles = source_masks_for_event(evt, masks)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        # CIAO region(file) filters accept these as sky/physical pixels from
        # the [sky=...] filter; adding a DS9/CIAO header made dmcoords reject
        # the file in CIAO 4.18 during blank-sky extraction.
        if inner_r500 > 0:
            f.write(f"annulus({x:.6f},{y:.6f},{inner_r500 * r_outer:.6f},{r_outer:.6f})\n")
        else:
            f.write(f"circle({x:.6f},{y:.6f},{r_outer:.6f})\n")
        for ex, ey, er_pix in exclude_circles:
            f.write(f"-circle({ex:.6f},{ey:.6f},{er_pix:.6f})\n")
    return path.resolve()


def write_local_background_region_for_event(
    path: Path,
    evt: Path,
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    masks: list[PointSourceMask],
    exclude_r500: float = DEFAULT_LOCAL_BKG_EXCLUDE_R500,
) -> Path:
    """Write a same-observation source-free background region.

    The region uses the detector sky extent in the event file and excludes the
    cluster out to ``exclude_r500`` plus all detected point sources. This is
    intended for ACIS-I observations where the paper reports source-free field
    area; ACIS-S observations keep using blank-sky background.
    """
    from astropy.io import fits

    x0, y0, pix_arcsec = sky_xy_from_event_wcs(evt, center_ra, center_dec)
    r_exclude = exclude_r500 * r500_arcsec / pix_arcsec
    exclude_circles = source_masks_for_event(evt, masks)
    with fits.open(evt) as hdul:
        data = hdul["EVENTS"].data
        xs = np.asarray(data["x"], dtype=float)
        ys = np.asarray(data["y"], dtype=float)
    xmin, xmax = float(np.nanmin(xs)), float(np.nanmax(xs))
    ymin, ymax = float(np.nanmin(ys)), float(np.nanmax(ys))
    pad = 8.0
    xcen = 0.5 * (xmin + xmax)
    ycen = 0.5 * (ymin + ymax)
    width = max(1.0, xmax - xmin - pad)
    height = max(1.0, ymax - ymin - pad)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(f"box({xcen:.6f},{ycen:.6f},{width:.6f},{height:.6f})\n")
        f.write(f"-circle({x0:.6f},{y0:.6f},{r_exclude:.6f})\n")
        for ex, ey, er_pix in exclude_circles:
            f.write(f"-circle({ex:.6f},{ey:.6f},{er_pix:.6f})\n")
    return path.resolve()


def run_specextract_one(
    cluster_dir: Path,
    evt: Path,
    bkg_evt: Path,
    src_region: Path,
    bkg_region: Path,
    outroot: Path,
    background_kind: str,
) -> Path | None:
    """Extract one source PHA with either local or blank-sky background."""
    if shutil.which("specextract") is None:
        print("[warn] CIAO specextract not found on PATH; skipping spectral extraction.")
        return None
    cmd = [
        "specextract",
        f"infile={evt}[sky=region({src_region})]",
        f"bkgfile={bkg_evt}[sky=region({bkg_region})]",
        f"outroot={outroot}",
        "correctpsf=no",
        f"weight={'yes' if DEFAULT_SPECEEXTRACT_WEIGHT else 'no'}",
        "bkgresp=no",
        "clobber=yes",
        "mode=h",
    ]
    try:
        run(cmd, cwd=cluster_dir)
    except subprocess.CalledProcessError as exc:
        print(f"[warn] specextract failed for {evt} with {background_kind} background {bkg_evt}: {exc}")
        return None
    pi = Path(str(outroot) + ".pi")
    return pi if pi.exists() else None


def build_background_plan_for_aperture(
    outdir: Path,
    name: str,
    label: str,
    evt2_by_obsid: dict[str, Path],
    blank_by_obsid: dict[str, Path],
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    inner_r500: float,
    outer_r500: float,
    masks: list[PointSourceMask],
) -> dict[str, Any]:
    """Create or refresh the per-ObsID aperture/background region metadata."""
    backgrounds: dict[str, Any] = {}
    region_dir = outdir / "regions" / "per_obs"
    for obsid, evt in evt2_by_obsid.items():
        src_region = write_aperture_region_for_event(
            region_dir / f"{name}_obs{obsid}_{label}_src_phys.reg",
            evt,
            center_ra,
            center_dec,
            r500_arcsec,
            inner_r500,
            outer_r500,
            masks,
        )
        if use_blanksky_for_obsid(evt):
            if obsid not in blank_by_obsid:
                raise SystemExit(f"No blank-sky file available for ObsID {obsid}")
            # CIAO blanksky reprojects the blank-sky events onto the science
            # observation, so the science aperture region is reused.
            bkg_event = blank_by_obsid[obsid]
            bkg_region = src_region
            background_kind = "blanksky"
        else:
            bkg_event = evt
            bkg_region = write_local_background_region_for_event(
                region_dir / f"{name}_obs{obsid}_{label}_bkg_local_phys.reg",
                evt,
                center_ra,
                center_dec,
                r500_arcsec,
                masks,
            )
            background_kind = "local_source_free_field"
        backgrounds[obsid] = {
            "kind": background_kind,
            "source_event_file": str(evt),
            "source_region_file": str(src_region),
            "background_event_file": str(bkg_event),
            "background_region_file": str(bkg_region),
        }
    return backgrounds


def extract_spectra_for_aperture(
    cluster_dir: Path,
    outdir: Path,
    name: str,
    label: str,
    evt2_by_obsid: dict[str, Path],
    blank_by_obsid: dict[str, Path],
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    inner_r500: float,
    outer_r500: float,
    masks: list[PointSourceMask],
) -> tuple[list[Path], dict[str, Any]]:
    spec_dir = outdir / "spectra" / label
    spec_dir.mkdir(parents=True, exist_ok=True)
    spectra: list[Path] = []
    backgrounds = build_background_plan_for_aperture(
        outdir,
        name,
        label,
        evt2_by_obsid,
        blank_by_obsid,
        center_ra,
        center_dec,
        r500_arcsec,
        inner_r500,
        outer_r500,
        masks,
    )
    for obsid, evt in evt2_by_obsid.items():
        background = backgrounds[obsid]
        outroot = spec_dir / f"{name}_obs{obsid}_{label}"
        pi = run_specextract_one(
            cluster_dir,
            evt,
            Path(background["background_event_file"]),
            Path(background["source_region_file"]),
            Path(background["background_region_file"]),
            outroot,
            background["kind"],
        )
        if pi is not None:
            spectra.append(pi.resolve())
    return spectra, backgrounds


def write_sherpa_fit_script(
    path: Path,
    spectra: list[Path],
    out_json: Path,
    out_plot: Path,
    z: float,
    nh_1e22: float,
    dl_cm: float,
    fit_band: tuple[float, float],
    soft_rest_band: tuple[float, float],
    bolo_rest_band: tuple[float, float],
    kt_init: float,
    abundance: float,
) -> None:
    spectra_literal = "[" + ", ".join(repr(str(p)) for p in spectra) + "]"
    path.write_text(f'''#!/usr/bin/env sherpa
from sherpa.astro.ui import *
import json
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

spectra = {spectra_literal}
if not spectra:
    raise SystemExit("No spectra supplied")

set_stat("wstat")
set_method("levmar")

gal = xsphabs.gal
icm = xsapec.icm
gal.nH = {nh_1e22:.8g}
gal.nH.freeze()
icm.redshift = {z:.8g}
icm.redshift.freeze()
icm.kT = {kt_init:.8g}
icm.Abundanc = {abundance:.8g}
icm.Abundanc.freeze()
icm.norm = 1e-3

for i, pha in enumerate(spectra, start=1):
    load_pha(i, pha)
    try:
        ignore_bad(i)
    except Exception:
        pass
    notice_id(i, {fit_band[0]:.8g}, {fit_band[1]:.8g})
    group_counts(i, 1)
    set_source(i, gal * icm)

fit()
conf_results = None
try:
    conf()
    conf_results = get_conf_results()
except Exception as exc:
    print("[warn] conf() failed:", exc)

soft_obs = ({soft_rest_band[0]:.8g} / (1 + {z:.8g}), {soft_rest_band[1]:.8g} / (1 + {z:.8g}))
bolo_obs = ({bolo_rest_band[0]:.8g} / (1 + {z:.8g}), {bolo_rest_band[1]:.8g} / (1 + {z:.8g}))
# model=icm gives unabsorbed APEC flux; id=1 gives absorbed source-model flux.
soft_flux_unabs = float(calc_energy_flux(soft_obs[0], soft_obs[1], model=icm))
soft_flux_abs = float(calc_energy_flux(soft_obs[0], soft_obs[1], id=1))
bolo_flux_unabs = float(calc_energy_flux(bolo_obs[0], bolo_obs[1], model=icm))
dl_cm = {dl_cm:.12g}
soft_lum_unabs = 4.0 * math.pi * dl_cm * dl_cm * soft_flux_unabs
bolo_lum_unabs = 4.0 * math.pi * dl_cm * dl_cm * bolo_flux_unabs

residual_summaries = []
plot_caveat = "WSTAT fit: plot/residuals are qualitative only; background PHA is used internally by WSTAT."
fig, (ax, rax) = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True, gridspec_kw={{"height_ratios": [3, 1], "hspace": 0.05}})
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, pha in enumerate(spectra, start=1):
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
        "plot_caveat": plot_caveat,
    }})
    ax.errorbar(dp.x, dp.y, yerr=getattr(dp, "yerr", None), fmt="o", ms=3, lw=0.8, alpha=0.75, color=color, label=f"{{label}} data")
    ax.plot(mp.x, mp.y, color=color, lw=1.5, label=f"{{label}} model")
    rax.axhline(0, color="0.25", ls="--", lw=0.8)
    rax.errorbar(rp.x, rp.y, yerr=getattr(rp, "yerr", None), fmt="o", ms=3, lw=0.8, alpha=0.75, color=color)
ax.set_yscale("log")
ax.set_ylabel("Counts s$^{{-1}}$ keV$^{{-1}}$")
rax.set_xlabel("Energy (keV)")
rax.set_ylabel("Residual")
ax.set_title("Joint absorbed APEC fit")
ax.text(0.02, 0.03, plot_caveat, transform=ax.transAxes, fontsize=8, bbox={{"facecolor": "white", "edgecolor": "0.7", "alpha": 0.85}})
ax.legend(fontsize=6, ncol=2)
ax.grid(alpha=0.2)
rax.grid(alpha=0.2)
fig.savefig("{out_plot}", dpi=180, bbox_inches="tight")
plt.close(fig)

fr = get_fit_results()
qa_flags = []
if getattr(fr, "rstat", None) is not None and fr.rstat > 1.5:
    qa_flags.append("high_reduced_statistic_inspect_model_background_or_calibration")
if getattr(fr, "qval", None) is not None and fr.qval < 0.01:
    qa_flags.append("low_q_value_fit_not_statistically_acceptable")
if icm.kT.val > 20:
    qa_flags.append("very_high_temperature_check_background_center_core_or_multitemperature_structure")
if icm.kT.val >= 63.5:
    qa_flags.append("temperature_pegged_at_xsapec_upper_bound")
confidence = {{}}
if conf_results is not None:
    for pname, pval, pmin, pmax in zip(conf_results.parnames, conf_results.parvals, conf_results.parmins, conf_results.parmaxes):
        confidence[str(pname)] = {{
            "best": None if pval is None else float(pval),
            "lower_delta_1sigma": None if pmin is None else float(pmin),
            "upper_delta_1sigma": None if pmax is None else float(pmax),
        }}
vals = {{
    "spectra": spectra,
    "n_spectra": len(spectra),
    "model": "xsphabs * xsapec",
    "statname": fr.statname,
    "statval": float(fr.statval),
    "dof": int(fr.dof),
    "rstat": None if getattr(fr, "rstat", None) is None else float(fr.rstat),
    "q_value": None if getattr(fr, "qval", None) is None else float(fr.qval),
    "temperature_keV": float(icm.kT.val),
    "abundance_solar": float(icm.Abundanc.val),
    "apec_norm": float(icm.norm.val),
    "nH_1e22_cm2": float(gal.nH.val),
    "redshift": float(icm.redshift.val),
    "confidence_intervals": confidence,
    "fit_band_keV": [{fit_band[0]:.8g}, {fit_band[1]:.8g}],
    "rest_soft_band_keV": [{soft_rest_band[0]:.8g}, {soft_rest_band[1]:.8g}],
    "rest_bolometric_band_keV": [{bolo_rest_band[0]:.8g}, {bolo_rest_band[1]:.8g}],
    "soft_flux_unabsorbed_erg_s_cm2": soft_flux_unabs,
    "soft_flux_absorbed_erg_s_cm2": soft_flux_abs,
    "bolometric_flux_unabsorbed_erg_s_cm2": bolo_flux_unabs,
    "soft_luminosity_unabsorbed_erg_s": soft_lum_unabs,
    "bolometric_luminosity_unabsorbed_erg_s": bolo_lum_unabs,
    "background_method": "{DEFAULT_BACKGROUND_MODE}: local ACIS-I source-free field where available; ACIS-S blank-sky; Sherpa WSTAT; no subtract()",
    "plot_caveat": plot_caveat,
    "residual_summaries": residual_summaries,
    "fit_plot_png": "{out_plot}",
    "qa_flags": qa_flags,
    "response_weighting": "{'yes' if DEFAULT_SPECEEXTRACT_WEIGHT else 'no'}",
}}
with open("{out_json}", "w") as f:
    json.dump(vals, f, indent=2, sort_keys=True)
print(json.dumps(vals, indent=2, sort_keys=True))
''')


def run_sherpa_fit(outdir: Path, label: str, spectra: list[Path], row: ClusterRow, h0: float, omega_m: float, kt_init: float) -> tuple[Path, Path, Path]:
    fit_dir = outdir / "fits" / label
    fit_dir.mkdir(parents=True, exist_ok=True)
    script = fit_dir / f"fit_{row.key}_{label}_sherpa.py"
    out_json = fit_dir / f"{row.key}_{label}_fit_results.json"
    out_plot = fit_dir / f"{row.key}_{label}_fit_plot.png"
    write_sherpa_fit_script(
        script,
        spectra,
        out_json,
        out_plot,
        row.z,
        row.nh_1e22,
        luminosity_distance_cm(row.z, h0, omega_m),
        DEFAULT_FIT_BAND,
        DEFAULT_SOFT_REST_BAND,
        DEFAULT_BOLO_REST_BAND,
        kt_init,
        DEFAULT_ABUNDANCE,
    )
    run(["sherpa", "-n", "-b", str(script)], cwd=fit_dir)
    return script, out_json, out_plot


def summarize_fit_result(path: Path | None, expected_kt_keV: float) -> dict[str, Any] | None:
    """Load compact science values from a fit JSON and add simple sanity checks."""
    if path is None or not path.exists():
        return None
    data = json.loads(path.read_text())
    kt = data.get("temperature_keV")
    flags = list(data.get("qa_flags") or [])
    if isinstance(kt, (int, float)):
        if kt > 1.5 * expected_kt_keV:
            flags.append("temperature_high_vs_simple_m500_scaling")
        if kt < 0.3 * expected_kt_keV:
            flags.append("temperature_low_vs_simple_m500_scaling")
    return {
        "temperature_keV": kt,
        "temperature_1sigma": data.get("confidence_intervals", {}).get("icm.kT"),
        "soft_luminosity_unabsorbed_erg_s": data.get("soft_luminosity_unabsorbed_erg_s"),
        "bolometric_luminosity_unabsorbed_erg_s": data.get("bolometric_luminosity_unabsorbed_erg_s"),
        "rstat": data.get("rstat"),
        "q_value": data.get("q_value"),
        "qa_flags": sorted(set(flags)),
        "fit_json": str(path),
        "fit_plot_png": data.get("fit_plot_png"),
        "n_spectra": data.get("n_spectra"),
        "response_weighting": data.get("response_weighting"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster-key", default=DEFAULT_CLUSTER_KEY)
    parser.add_argument("--cluster-dir", type=Path, default=DEFAULT_CLUSTER_DIR)
    parser.add_argument("--cluster-table", type=Path, default=DEFAULT_CLUSTER_TABLE)
    parser.add_argument("--output-dirname", default=DEFAULT_OUTPUT_DIRNAME)
    parser.add_argument("--no-run-repro", action="store_true")
    parser.add_argument("--no-run-imaging", action="store_true")
    parser.add_argument("--no-run-blanksky", action="store_true")
    parser.add_argument("--no-run-specextract", action="store_true")
    parser.add_argument("--no-run-sherpa", action="store_true")
    parser.add_argument("--run-csmooth", action="store_true", help="Run CIAO csmooth for display; default uses merged image directly because csmooth can be slow")
    args = parser.parse_args()

    row = read_cluster_table(args.cluster_table, args.cluster_key)
    cluster_dir = args.cluster_dir.resolve()
    outdir = cluster_dir / args.output_dirname
    outdir.mkdir(parents=True, exist_ok=True)
    results_dir = outdir / "results"
    results_dir.mkdir(exist_ok=True)

    r500_mpc = compute_r500_mpc(row.m500_msun, row.z, DEFAULT_H0, DEFAULT_OMEGA_M)
    r500_arcsec = angular_radius_arcsec(r500_mpc, row.z, DEFAULT_H0, DEFAULT_OMEGA_M)
    kt_init = 5.0 * (row.m500_msun / 3e14) ** (2.0 / 3.0)

    evt2_by_obsid = reprocess_obsids(cluster_dir, row.obsids, not args.no_run_repro)
    imaging_info = run_merge_obs(list(evt2_by_obsid.values()), outdir / "imaging") if not args.no_run_imaging else {"products": []}
    img_for_sources = choose_image(outdir / "imaging", "thresh") or choose_image(outdir / "imaging", "flux")
    if img_for_sources is None:
        raise SystemExit("No merged image found for wavdetect/aperture visualization")
    img_for_display_raw = choose_image(outdir / "imaging", "flux") or img_for_sources
    img_for_display = make_smoothed_display_image(img_for_display_raw, outdir / "imaging")
    src_fits = run_wavdetect(img_for_sources, outdir / "imaging")
    smoothed = run_csmooth(img_for_display, outdir / "imaging") if args.run_csmooth else img_for_display

    peak = find_xray_peak_center(smoothed, row.ra, row.dec, DEFAULT_XRAY_PEAK_SEARCH_ARCSEC)
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
        max_radius_r500=1.0,
        sigma_min=DEFAULT_POINT_SOURCE_SIGMA_MIN,
        radius_scale=DEFAULT_POINT_SOURCE_RADIUS_SCALE,
        min_radius_pix=DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX,
        skip_center_r500=DEFAULT_POINT_SOURCE_SKIP_CENTER_R500,
    )

    if args.no_run_blanksky:
        blank_by_obsid = load_existing_blanksky_for_obsids(evt2_by_obsid, outdir / "blanksky")
    else:
        blank_by_obsid = run_blanksky_for_obsids(evt2_by_obsid, cluster_dir, outdir / "blanksky", require=True)

    apertures = [
        ("full_r500", 0.0, 1.0),
        ("core_excised_0p15_0p5r500", DEFAULT_CORE_INNER_R500, 0.5),
        ("core_excised_0p15_1r500", DEFAULT_CORE_INNER_R500, 1.0),
    ]
    aperture_products: list[ApertureProduct] = []
    fit_comparison: dict[str, Any] = {}
    for label, inner_r500, outer_r500 in apertures:
        region_path = outdir / "regions" / f"{row.key}_{label}_src.reg"
        region_path.parent.mkdir(parents=True, exist_ok=True)
        write_region(region_path, center_ra, center_dec, outer_r500 * r500_arcsec, inner_r500 * r500_arcsec if inner_r500 > 0 else None)
        plot_path = outdir / "figures" / f"{row.key}_{label}_aperture_overlay.png"
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        aperture_plot = write_aperture_overlay_plot(
            smoothed,
            plot_path,
            center_ra,
            center_dec,
            r500_arcsec,
            0.0,
            0.0,
            inner_r500,
            masks,
            f"{row.key} {label} aperture",
            source_outer_r500=outer_r500,
        )
        spectra: list[Path] = []
        background_by_obsid: dict[str, Any] = {}
        if not args.no_run_specextract:
            spectra, background_by_obsid = extract_spectra_for_aperture(cluster_dir, outdir, row.key, label, evt2_by_obsid, blank_by_obsid, center_ra, center_dec, r500_arcsec, inner_r500, outer_r500, masks)
        else:
            background_by_obsid = build_background_plan_for_aperture(
                outdir,
                row.key,
                label,
                evt2_by_obsid,
                blank_by_obsid,
                center_ra,
                center_dec,
                r500_arcsec,
                inner_r500,
                outer_r500,
                masks,
            )
            spectra = [
                p
                for p in sorted((outdir / "spectra" / label).glob(f"{row.key}_obs*_{label}.pi"))
                if not p.name.endswith(("_bkg.pi", "_grp.pi"))
            ]
        sherpa_script = fit_json = fit_plot = None
        if not args.no_run_sherpa and spectra:
            sherpa_script, fit_json, fit_plot = run_sherpa_fit(outdir, label, spectra, row, DEFAULT_H0, DEFAULT_OMEGA_M, kt_init)
        if fit_json:
            fit_comparison[label] = summarize_fit_result(Path(fit_json), kt_init)
        aperture_products.append(ApertureProduct(label, inner_r500, outer_r500, [str(p) for p in spectra], str(sherpa_script) if sherpa_script else None, str(fit_json) if fit_json else None, str(fit_plot) if fit_plot else None, str(aperture_plot) if aperture_plot else None, str(region_path), background_by_obsid or None))

    adopted_no_core_label = "core_excised_0p15_0p5r500"
    adopted_no_core = fit_comparison.get(adopted_no_core_label)

    summary = {
        "cluster": asdict(row),
        "cluster_dir": str(cluster_dir),
        "output_dir": str(outdir),
        "r500_mpc": r500_mpc,
        "r500_arcsec": r500_arcsec,
        "center_mode": center_mode,
        "catalog_center_ra_deg": row.ra,
        "catalog_center_dec_deg": row.dec,
        "fit_center_ra_deg": center_ra,
        "fit_center_dec_deg": center_dec,
        "center_offset_from_catalog_arcsec": center_offset,
        "m500_source": "cluster_center_table.csv lensing M500c",
        "expected_temperature_keV_simple_m500_scaling": kt_init,
        "physical_reasonableness_note": "Hybrid local/blank-sky background gives physically finite full-R500 and 0.15-0.5R500 temperatures. The larger 0.15-1.0R500 core-excised aperture remains background-dominated and should not be used as the adopted T_X.",
        "adopted_no_core_temperature_aperture": adopted_no_core_label,
        "adopted_no_core_temperature_result": adopted_no_core,
        "background_method": f"{DEFAULT_BACKGROUND_MODE}: local ACIS-I source-free field where available; ACIS-S blank-sky; Sherpa WSTAT; no subtract()",
        "specextract_weight_response": DEFAULT_SPECEEXTRACT_WEIGHT,
        "evt2_by_obsid": {k: str(v) for k, v in evt2_by_obsid.items()},
        "blanksky_by_obsid": {k: str(v) for k, v in blank_by_obsid.items()},
        "imaging": imaging_info,
        "source_catalog": str(src_fits),
        "source_detection_image": str(img_for_sources),
        "display_flux_image": str(img_for_display),
        "smoothed_image": str(smoothed),
        "point_source_mask_count": len(masks),
        "apertures": [asdict(p) for p in aperture_products],
        "fit_comparison": fit_comparison,
    }
    summary_path = results_dir / f"{row.key}_pipeline_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("\nWrote summary:", summary_path)


if __name__ == "__main__":
    main()
