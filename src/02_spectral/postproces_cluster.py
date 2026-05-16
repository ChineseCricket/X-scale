#!/usr/bin/env python3
"""Post-process one Chandra cluster directory for Lx-M500 / Tx-M500 work.

This script is designed for a processed CIAO directory such as ``cluster209``.
It can:

1. Compute R500 from an independent M500 and redshift.
2. Write DS9/CIAO source and background regions for R500 spectral extraction.
3. Measure aperture flux and luminosity from an exposure-corrected flux image.
4. Optionally call CIAO ``specextract`` for each individual exposure and write
   a Sherpa joint-fitting script for an absorbed thermal plasma model. Spectra
   are not extracted from the merged event file, because a merged event file
   does not have a physically valid single ARF/RMF response.

Notes
-----
- The luminosity from a broad-band flux image is an observed-band luminosity:
  L = 4*pi*D_L^2*F. It is not a rest-frame/k-corrected luminosity.
- The robust temperature measurement requires CIAO/Sherpa and per-exposure
  response files.
- The normal science choices live in the constants near the top of this file
  and in ``cluster_center_table.csv``. CLI arguments are optional overrides.

Example
-------
python postprocess_cluster.py

The default cluster is controlled by ``DEFAULT_CLUSTER_KEY``. Cluster centers,
redshifts, masses, and ObsIDs are read from ``cluster_center_table.csv``.

Full English / zh-CN documentation is in
``postprocess_cluster_documentation_bilingual.md``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

try:
    import astropy.units as u
    from astropy.io import fits
    from astropy.wcs import WCS
    from astropy.coordinates import SkyCoord
except ModuleNotFoundError as exc:  # pragma: no cover - friendly runtime error
    raise SystemExit(
        "Missing Python dependency. Install with:\n"
        "  python3 -m pip install astropy numpy\n"
        f"Original import error: {exc}"
    )

G_CGS = 6.67430e-8
MSUN_G = 1.98847e33
MPC_CM = 3.0856775814913673e24
C_KM_S = 299792.458

# ---------------------------------------------------------------------------
# Normal run settings
# ---------------------------------------------------------------------------
# For day-to-day use, edit these constants and the CSV table instead of typing
# long command lines. CLI flags still exist as optional overrides.
# Input path settings. Relative paths are interpreted relative to the current
# project directory or, for files inside a cluster, relative to DEFAULT_CLUSTER_DIR.
DEFAULT_CLUSTER_KEY = "Abell_0209"
DEFAULT_CLUSTER_DIR = Path("")
CLUSTER_TABLE_PATH = Path("configs/cluster_table.csv")
DEFAULT_INDIVIDUAL_EVT_GLOB = "raw/*/repro/*_repro_evt2.fits"
DEFAULT_MERGED_EVT = "processed/merged_clean_evt.fits"
DEFAULT_FLUX_IMAGE = "processed/clean_fluxed/flux_clean.img"
DEFAULT_APERTURE_PLOT_IMAGE = "processed/clean_fluxed/flux_csmooth.img"
DEFAULT_POINT_SOURCE_FILE = "processed/src.fits"

# Run behavior and science settings.
DEFAULT_RUN_SPECEXTRACT = False
DEFAULT_RUN_SHERPA = False
DEFAULT_SHERPA_BACKGROUND_MODE = "wstat"  # allowed: wstat, subtract
DEFAULT_ENERGY_MIN_KEV = 0.5
DEFAULT_ENERGY_MAX_KEV = 7.0
DEFAULT_BKG_INNER_R500 = 1.2
DEFAULT_BKG_OUTER_R500 = 1.8
DEFAULT_EXCISE_CORE = False
DEFAULT_CORE_INNER_R500 = 0.15
DEFAULT_CENTER_MODE = "xray_peak"  # allowed: catalog, xray_peak, manual
DEFAULT_XRAY_PEAK_SEARCH_ARCSEC = 120.0
DEFAULT_MASK_POINT_SOURCES = True
DEFAULT_POINT_SOURCE_SIGMA_MIN = 5.0
DEFAULT_POINT_SOURCE_RADIUS_SCALE = 2.0
DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX = 6.0
DEFAULT_POINT_SOURCE_SKIP_CENTER_R500 = 0.05
DEFAULT_SPECEXTRACT_CORRECTPSF = "no"
# ``weight=yes`` calls mkwarf over the full extended aperture. That is more
# spatially exact, but it can be extremely slow for a large R500 region.
# ``weight=no`` uses a single response at the aperture center and is the
# practical default for fast, repeatable batch post-processing.
DEFAULT_SPECEXTRACT_WEIGHT = "no"
DEFAULT_SPECEXTRACT_BKGRESP = "no"

# Data-directory aliases for hand-processed folders whose names differ from
# the catalog key. The default search also checks chandra_data_evt/<key> and
# data/raw/<key>, so most clusters don't need an entry here.
CLUSTER_DATA_DIRS = {
    "Abell_0209": "cluster209",
    "Abell_209": "cluster209",
}


@dataclass
class ClusterConfig:
    name: str
    aliases: tuple[str, ...]
    center_ra: float
    center_dec: float
    obsids: tuple[str, ...]
    redshift: float | None = None
    m500: float | None = None
    m500_h_inverse: bool = False
    h0: float = 70.0
    omega_m: float = 0.3
    nh_1e22: float = 0.0165
    data_dir: str | None = None


def cluster_key(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name).strip("_")


CLUSTER_CONFIGS: dict[str, ClusterConfig] = {
    "Abell_383": ClusterConfig(name="Abell 383", aliases=("ACO 383", "ABELL 383", "Abell 0383"), center_ra=42.01413120, center_dec=-3.52923000, obsids=("524", "2320", "2321"), redshift=0.187, m500=5.88e14),
    "Abell_209": ClusterConfig(name="Abell 209", aliases=("ACO 209", "ABELL 209", "Abell 0209"), center_ra=22.97030000, center_dec=-13.61470000, obsids=("3579", "522"), redshift=0.206, m500=9.64e14, data_dir="cluster209"),
    "Abell_2261": ClusterConfig(name="Abell 2261", aliases=("ACO 2261", "ABELL 2261"), center_ra=260.61200000, center_dec=32.13280000, obsids=("550", "20413", "21960", "5007"), redshift=0.224, m500=15.65e14),
    "RXJ2129_7_0005": ClusterConfig(name="RXJ2129.7+0005", aliases=("RX J2129.7+0005", "RXCJ2129.7+0005"), center_ra=322.41875000, center_dec=0.09638889, obsids=("9370", "552"), redshift=0.234, m500=4.48e14),
    "Abell_611": ClusterConfig(name="Abell 611", aliases=("ACO 611", "ABELL 611", "Abell 0611"), center_ra=120.24458333, center_dec=36.04694444, obsids=("3194",), redshift=0.288, m500=10.73e14),
    "MS2137_2353": ClusterConfig(name="MS2137-2353", aliases=("MS 2137-2353", "MS 2137.3-2353"), center_ra=325.05333333, center_dec=-23.65750000, obsids=("4974", "5250", "928"), redshift=0.313, m500=8.28e14),
    "RXJ2248_7_4431": ClusterConfig(name="RXJ2248.7-4431", aliases=("RXCJ2248.7-4431", "Abell S1063", "AS1063"), center_ra=342.18900000, center_dec=-44.52820000, obsids=("18611", "18818", "4966"), redshift=0.348, m500=12.45e14),
    "MACSJ1115_9_0129": ClusterConfig(name="MACSJ1115.9+0129", aliases=("MACS J1115.9+0129", "MACS J1115.8+0129"), center_ra=168.96626000, center_dec=1.49863000, obsids=("9375", "3275"), redshift=0.352, m500=10.67e14),
    "MACSJ1931_8_2635": ClusterConfig(name="MACSJ1931.8-2635", aliases=("MACS J1931.8-2634", "MACS J1931.8-2635"), center_ra=292.95000000, center_dec=-26.58333300, obsids=("9382", "3282"), redshift=0.352, m500=10.51e14),
    "RXJ1532_9_3021": ClusterConfig(name="RXJ1532.9+3021", aliases=("RX J1532.9+3021",), center_ra=233.22408200, center_dec=30.34983600, obsids=("14009", "1649", "1665"), redshift=0.363, m500=4.17e14),
    "MACSJ1720_3_3536": ClusterConfig(name="MACSJ1720.3+3536", aliases=("MACS J1720.3+3536",), center_ra=260.06989000, center_dec=35.60736000, obsids=("3280", "6107", "7225", "7718"), redshift=0.391, m500=9.96e14),
    "MACSJ0429_6_0253": ClusterConfig(name="MACSJ0429.6-0253", aliases=("MACS J0429.6-0253",), center_ra=67.39980000, center_dec=-2.88505800, obsids=("3271",), redshift=0.399, m500=6.85e14),
    "MACSJ1206_2_0847": ClusterConfig(name="MACSJ1206.2-0847", aliases=("MACS J1206.2-0847",), center_ra=181.54991000, center_dec=-8.80001000, obsids=("3277", "20544", "20929", "21078", "21079", "21081"), redshift=0.440, m500=12.24e14),
    "MACSJ0329_7_0211": ClusterConfig(name="MACSJ0329.7-0211", aliases=("MACS J0329.7-0211",), center_ra=52.42000000, center_dec=-2.19833300, obsids=("3582", "6108", "7719", "3257"), redshift=0.450, m500=6.51e14),
    "RXJ1347_5_1145": ClusterConfig(name="RXJ1347.5-1145", aliases=("RX J1347.5-1145", "RXCJ1347.5-1145"), center_ra=206.87700000, center_dec=-11.75190000, obsids=("3592", "13999", "14407", "506", "507", "2222", "13516"), redshift=0.451, m500=22.33e14),
    "MACSJ0744_9_3927": ClusterConfig(name="MACSJ0744.9+3927", aliases=("MACS J0744.9+3927",), center_ra=116.21862500, center_dec=39.45759400, obsids=("3197", "6111", "3585"), redshift=0.686, m500=11.94e14),
    "MACSJ0416_1_2403": ClusterConfig(name="MACSJ0416.1-2403", aliases=("MACS J0416.1-2403",), center_ra=64.03848800, center_dec=-24.06887100, obsids=("16236", "16237", "16523", "17313", "10446", "16304"), redshift=0.396, m500=6.85e14),
    "MACSJ1149_5_2223": ClusterConfig(name="MACSJ1149.5+2223", aliases=("MACS J1149.5+2223",), center_ra=177.39622100, center_dec=22.40303900, obsids=("1656", "3589", "16306", "16582", "16238", "16239", "17595", "17596"), redshift=0.544, m500=14.57e14),
    "MACSJ0717_5_3745": ClusterConfig(name="MACSJ0717.5+3745", aliases=("MACS J0717.5+3745",), center_ra=109.37886200, center_dec=37.75826100, obsids=("4200", "16235", "16305", "1655"), redshift=0.548, m500=14.98e14),
    "MACSJ0647_7_7015": ClusterConfig(name="MACSJ0647.7+7015", aliases=("MACS J0647.7+7015",), center_ra=101.96028800, center_dec=70.24859700, obsids=("3584", "3196"), redshift=0.584, m500=9.49e14),
    "Abell_0068": ClusterConfig(name="Abell 0068", aliases=("Abell 68", "ABELL0068", "ABELL 68", "ACO 68"), center_ra=9.27583333, center_dec=9.15916667, obsids=("3250",), redshift=0.2546, m500=4.78e14, m500_h_inverse=True, nh_1e22=0.0460),
    "Abell_2813": ClusterConfig(name="Abell 2813", aliases=("ABELL2813", "ABELL 2813", "ACO 2813"), center_ra=10.84520000, center_dec=-20.62260000, obsids=("16278", "9409", "15093", "15094", "15095", "16366", "16491", "16513"), redshift=0.2924, m500=5.90e14, m500_h_inverse=True, nh_1e22=0.0155),
    "Abell_0115": ClusterConfig(name="Abell 0115", aliases=("Abell 115", "ABELL0115", "ABELL 115", "ACO 115"), center_ra=13.99500000, center_dec=26.38700000, obsids=("13458", "13459", "15578", "15581", "3233"), redshift=0.1952, m500=3.77e14, m500_h_inverse=True, nh_1e22=0.0571),
    "Abell_0141": ClusterConfig(name="Abell 0141", aliases=("Abell 141", "ABELL0141", "ABELL 141", "ACO 141"), center_ra=16.40492800, center_dec=-24.68054100, obsids=("9410", "26070", "26092", "26093", "26094", "26095", "27465", "27466"), redshift=0.2300, m500=3.19e14, m500_h_inverse=True, nh_1e22=0.0167),
    "Abell_0209": ClusterConfig(name="Abell 0209", aliases=("Abell 209", "ABELL0209", "ABELL 209", "ACO 209"), center_ra=22.97030000, center_dec=-13.61470000, obsids=("3579", "522"), redshift=0.2060, m500=8.64e14, m500_h_inverse=True, nh_1e22=0.0165, data_dir="cluster209"),
    "Abell_0267": ClusterConfig(name="Abell 0267", aliases=("Abell 267", "ABELL0267", "ABELL 267", "ACO 267"), center_ra=28.17923333, center_dec=0.99969444, obsids=("3580", "523", "1448", "1517"), redshift=0.2300, m500=3.92e14, m500_h_inverse=True, nh_1e22=0.0274),
    "Abell_0383": ClusterConfig(name="Abell 0383", aliases=("Abell 383", "ABELL0383", "ABELL 383", "ACO 383"), center_ra=42.01413120, center_dec=-3.52923000, obsids=("524", "2320", "2321"), redshift=0.1870, m500=3.64e14, m500_h_inverse=True, nh_1e22=0.0412),
    "Abell_0521": ClusterConfig(name="Abell 0521", aliases=("Abell 521", "ABELL0521", "ABELL 521", "ACO 521"), center_ra=73.53583333, center_dec=-10.24416667, obsids=("12880", "13190", "901", "430"), redshift=0.2533, m500=3.77e14, m500_h_inverse=True, nh_1e22=0.0617),
    "Abell_0586": ClusterConfig(name="Abell 0586", aliases=("Abell 586", "ABELL0586", "ABELL 586", "ACO 586"), center_ra=113.08458333, center_dec=31.63277778, obsids=("18278", "18279", "19961", "19962", "19963", "20003", "20004", "11723", "530"), redshift=0.1710, m500=5.04e14, m500_h_inverse=True, nh_1e22=0.0471),
    "Abell_0611": ClusterConfig(name="Abell 0611", aliases=("Abell 611", "ABELL0611", "ABELL 611", "ACO 611"), center_ra=120.24458333, center_dec=36.04694444, obsids=("3194",), redshift=0.2880, m500=6.37e14, m500_h_inverse=True, nh_1e22=0.0499),
    "Abell_0697": ClusterConfig(name="Abell 0697", aliases=("Abell 697", "ABELL0697", "ABELL 697", "ACO 697"), center_ra=130.74000000, center_dec=36.36250000, obsids=("532", "4217"), redshift=0.2820, m500=13.14e14, m500_h_inverse=True, nh_1e22=0.0334),
    "ZwCl_0857_9_2107": ClusterConfig(name="ZwCl 0857.9+2107", aliases=("ZwCl0857.9+2107",), center_ra=135.16250000, center_dec=20.92138900, obsids=("10463", "7897"), redshift=0.2350, m500=5.59e14, m500_h_inverse=True, nh_1e22=0.0338),
    "Abell_0750": ClusterConfig(name="Abell 0750", aliases=("Abell 750", "ABELL0750", "ABELL 750", "ACO 750"), center_ra=137.27791667, center_dec=11.03000000, obsids=("7699", "924"), redshift=0.1630, m500=3.17e14, m500_h_inverse=True, nh_1e22=0.0360),
}


def parse_optional_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def load_cluster_configs_from_table(path: Path = CLUSTER_TABLE_PATH) -> dict[str, ClusterConfig]:
    """Load cluster defaults from the CSV table, falling back to embedded configs."""
    if not path.exists():
        return CLUSTER_CONFIGS

    configs: dict[str, ClusterConfig] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["cluster_key"].strip()
            aliases = tuple(a.strip() for a in row.get("aliases", "").split(";") if a.strip())
            obsids = tuple(o.strip() for o in row.get("obsids", "").split(";") if o.strip())
            m500 = parse_optional_float(row.get("m500_input"))
            m500_unit = row.get("m500_unit", "").strip().lower()
            configs[key] = ClusterConfig(
                name=row.get("cluster_name", key).strip() or key,
                aliases=aliases,
                center_ra=float(row["ra_deg"]),
                center_dec=float(row["dec_deg"]),
                obsids=obsids,
                redshift=parse_optional_float(row.get("redshift")),
                m500=m500,
                m500_h_inverse=("h^-1" in m500_unit or "h-1" in m500_unit),
                data_dir=CLUSTER_DATA_DIRS.get(key),
            )
    return configs or CLUSTER_CONFIGS


def resolve_cluster_config(name: str, configs: dict[str, ClusterConfig]) -> tuple[str, ClusterConfig]:
    requested = cluster_key(name)
    if requested in configs:
        return requested, configs[requested]
    lower = name.lower()
    for key, cfg in configs.items():
        names = (cfg.name, *cfg.aliases)
        if any(lower == candidate.lower() or requested == cluster_key(candidate) for candidate in names):
            return key, cfg
    raise SystemExit(f"Unknown cluster {name!r}. Use --list-clusters to see valid keys.")


def default_cluster_dir(config_key: str, config: ClusterConfig) -> Path | None:
    candidates: list[Path] = []
    if DEFAULT_CLUSTER_DIR and DEFAULT_CLUSTER_DIR != Path(""):
        candidates.append(DEFAULT_CLUSTER_DIR)
    if config.data_dir:
        candidates.append(Path(config.data_dir))
    name_underscore = config.name.replace(" ", "_")
    candidates.extend(
        [
            Path("chandra_data_evt") / config_key,
            Path("data/raw") / config_key,
            Path("chandra_data_evt") / name_underscore,
            Path("data/raw") / name_underscore,
            Path("chandra_data_evt") / config.name,
            Path(config_key),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@dataclass
class ClusterResult:
    name: str
    cluster_dir: str
    redshift: float
    m500_msun: float
    r500_mpc: float
    r500_arcsec: float
    source_inner_r500: float
    source_inner_arcsec: float
    core_excised: bool
    center_mode: str
    catalog_center_ra_deg: float
    catalog_center_dec_deg: float
    center_ra_deg: float
    center_dec_deg: float
    center_offset_from_catalog_arcsec: float
    point_source_mask_file: str | None
    point_source_mask_count: int
    point_source_mask_sigma_min: float | None
    flux_image: str | None
    aperture_plot_image: str | None
    aperture_flux_erg_s_cm2: float | None
    aperture_flux_note: str | None
    aperture_luminosity_erg_s: float | None
    net_counts_r500: int | None
    bkg_counts_region: int | None
    source_region: str
    background_region: str
    aperture_plot_png: str | None
    individual_event_files: list[str]
    spectrum_pis: list[str]
    sherpa_background_mode: str
    sherpa_script: str
    fit_results_json: str
    fit_plot_png: str


@dataclass
class PointSourceMask:
    ra: float
    dec: float
    radius_arcsec: float
    significance: float
    net_counts: float
    separation_arcsec: float


def e_z(z: float, omega_m: float) -> float:
    return math.sqrt(omega_m * (1.0 + z) ** 3 + (1.0 - omega_m))


def critical_density_cgs(z: float, h0: float, omega_m: float) -> float:
    # H0 [km/s/Mpc] -> [s^-1]
    h_z = h0 * e_z(z, omega_m) * 1.0e5 / MPC_CM
    return 3.0 * h_z * h_z / (8.0 * math.pi * G_CGS)


def compute_r500_mpc(m500_msun: float, z: float, h0: float, omega_m: float) -> float:
    rho_c = critical_density_cgs(z, h0, omega_m)
    r_cm = (3.0 * m500_msun * MSUN_G / (4.0 * math.pi * 500.0 * rho_c)) ** (1.0 / 3.0)
    return r_cm / MPC_CM


def comoving_distance_mpc(z: float, h0: float, omega_m: float, ngrid: int = 4096) -> float:
    """Flat LCDM line-of-sight comoving distance without requiring scipy."""
    zz = np.linspace(0.0, z, ngrid + 1)
    inv_e = 1.0 / np.sqrt(omega_m * (1.0 + zz) ** 3 + (1.0 - omega_m))
    return (C_KM_S / h0) * float(np.trapezoid(inv_e, zz))


def angular_diameter_distance_mpc(z: float, h0: float, omega_m: float) -> float:
    return comoving_distance_mpc(z, h0, omega_m) / (1.0 + z)


def luminosity_distance_cm(z: float, h0: float, omega_m: float) -> float:
    return comoving_distance_mpc(z, h0, omega_m) * (1.0 + z) * MPC_CM


def angular_radius_arcsec(r_mpc: float, z: float, h0: float, omega_m: float) -> float:
    da = angular_diameter_distance_mpc(z, h0, omega_m)
    return (r_mpc / da) * 206264.806247


def choose_flux_image(cluster_dir: Path, requested: str | None) -> Path | None:
    if requested:
        p = Path(requested)
        return p if p.is_absolute() else cluster_dir / p
    candidates = [
        cluster_dir / "clean_fluxed" / "flux_clean.img",
        cluster_dir / "broad_flux.img",
        cluster_dir / "ciao_products" / "Abell_0209_merged.fits",
    ]
    for p in candidates:
        if p.exists():
            return p
    found = sorted(cluster_dir.glob("*flux*.img"))
    return found[0] if found else None


def choose_aperture_plot_image(cluster_dir: Path, flux_image: Path | None, requested: str | None) -> Path | None:
    """Prefer a smoothed/counts image for human-readable aperture overlays."""
    if requested:
        p = Path(requested)
        return p if p.is_absolute() else cluster_dir / p
    candidates = [
        cluster_dir / "clean_fluxed" / "flux_csmooth.img",
        cluster_dir / "merged_counts.img",
        cluster_dir / "broad_flux.img",
        flux_image,
        cluster_dir / "ciao_products" / "Abell_0209_smoothed.img",
    ]
    for p in candidates:
        if p is not None and p.exists():
            return p
    return None


def as_skycoord(obj: Any) -> SkyCoord:
    """Normalize Astropy WCS world output to a SkyCoord."""
    if isinstance(obj, SkyCoord):
        return obj
    if isinstance(obj, tuple):
        return SkyCoord(obj[0], obj[1])
    return SkyCoord(obj)


def find_xray_peak_center(
    image_path: Path | None,
    seed_ra: float,
    seed_dec: float,
    search_arcsec: float,
) -> tuple[float, float, float] | None:
    """Find the brightest smoothed X-ray pixel near the catalog/manual seed."""
    if image_path is None or not image_path.exists():
        return None

    seed = SkyCoord(ra=seed_ra * u.deg, dec=seed_dec * u.deg)
    with fits.open(image_path) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        data = np.asarray(hdu.data, dtype=float)
        wcs = WCS(hdu.header)
        x0, y0 = wcs.world_to_pixel(seed)
        pix_arcsec = abs(float(hdu.header.get("CDELT2", hdu.header.get("CDELT1", 0.00013666666666667)))) * 3600.0
        search_pix = max(1.0, search_arcsec / pix_arcsec)
        yy, xx = np.indices(data.shape)
        mask = np.isfinite(data) & (data > 0) & (np.hypot(xx - x0, yy - y0) <= search_pix)
        if not np.any(mask):
            return None
        peak_y, peak_x = np.unravel_index(np.argmax(np.where(mask, data, -np.inf)), data.shape)
        peak = as_skycoord(wcs.pixel_to_world(float(peak_x), float(peak_y)))
        offset_arcsec = float(seed.separation(peak).to_value(u.arcsec))
        return float(peak.ra.deg), float(peak.dec.deg), offset_arcsec


def resolve_analysis_center(
    mode: str,
    catalog_ra: float,
    catalog_dec: float,
    manual_ra: float | None,
    manual_dec: float | None,
    peak_image: Path | None,
    peak_search_arcsec: float,
) -> tuple[float, float, float, str]:
    """Resolve the actual center used for regions, counts, extraction, and plots."""
    normalized = mode.lower().strip()
    if normalized not in {"catalog", "xray_peak", "manual"}:
        raise SystemExit(f"Unknown center mode {mode!r}; use catalog, xray_peak, or manual.")

    if normalized == "manual":
        if manual_ra is None or manual_dec is None:
            raise SystemExit("--center-mode manual requires both --center-ra and --center-dec.")
        center_ra, center_dec = manual_ra, manual_dec
        actual_mode = "manual"
    elif normalized == "catalog":
        center_ra, center_dec = catalog_ra, catalog_dec
        actual_mode = "catalog"
    else:
        seed_ra = manual_ra if manual_ra is not None else catalog_ra
        seed_dec = manual_dec if manual_dec is not None else catalog_dec
        peak = find_xray_peak_center(peak_image, seed_ra, seed_dec, peak_search_arcsec)
        if peak is None:
            print("[warn] X-ray peak center could not be measured; falling back to catalog/manual seed center.")
            center_ra, center_dec = seed_ra, seed_dec
            actual_mode = "xray_peak_fallback_seed"
        else:
            center_ra, center_dec, _ = peak
            actual_mode = "xray_peak"

    catalog = SkyCoord(ra=catalog_ra * u.deg, dec=catalog_dec * u.deg)
    chosen = SkyCoord(ra=center_ra * u.deg, dec=center_dec * u.deg)
    offset_arcsec = float(catalog.separation(chosen).to_value(u.arcsec))
    return center_ra, center_dec, offset_arcsec, actual_mode


def image_sum_in_sky_annulus(
    image_path: Path,
    ra: float,
    dec: float,
    outer_arcsec: float,
    inner_arcsec: float = 0.0,
    point_source_masks: list[PointSourceMask] | None = None,
) -> tuple[float, str]:
    with fits.open(image_path) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        data = np.asarray(hdu.data, dtype=float)
        wcs = WCS(hdu.header)
        y_idx, x_idx = np.indices(data.shape)
        sky = wcs.pixel_to_world(x_idx, y_idx)
        center = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
        sep = center.separation(sky).arcsec
        mask = (sep <= outer_arcsec) & (sep >= inner_arcsec)
        for src in point_source_masks or []:
            src_center = SkyCoord(ra=src.ra * u.deg, dec=src.dec * u.deg)
            mask &= src_center.separation(sky).arcsec > src.radius_arcsec
        values = data[mask]
        values = values[np.isfinite(values)]
        summed = float(values.sum())
        bunit = str(hdu.header.get("BUNIT", "")).strip()
        if "erg" not in bunit.lower():
            # CIAO fluximage maps are commonly photon flux maps at a monochromatic
            # energy. Convert photon flux to approximate energy flux for Lx.
            mono_kev = float(hdu.header.get("ENERG_LO", hdu.header.get("E_MIN", 1.0)))
            summed *= mono_kev * 1.602176634e-9
            bunit = f"approx erg/s/cm2 from photon flux at {mono_kev:g} keV"
        return summed, bunit


def image_sum_in_sky_circle(image_path: Path, ra: float, dec: float, radius_arcsec: float) -> tuple[float, str]:
    return image_sum_in_sky_annulus(image_path, ra, dec, radius_arcsec, 0.0)


def sky_xy_from_image_wcs(image_path: Path, ra: float, dec: float) -> tuple[float, float, float]:
    """Return Chandra physical sky x/y and pixel scale from a CIAO image."""
    with fits.open(image_path) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        header = hdu.header
        wcs = WCS(header)
        img_x0, img_y0 = wcs.world_to_pixel(SkyCoord(ra=ra * u.deg, dec=dec * u.deg))
        # Astropy gives 0-based image pixels; CIAO physical coordinates are 1-based
        # image coordinates minus the LTV offset.
        phys_x = (float(img_x0) + 1.0) - float(header.get("LTV1", 0.0))
        phys_y = (float(img_y0) + 1.0) - float(header.get("LTV2", 0.0))
        pix_arcsec = abs(float(header.get("CDELT2", header.get("CDELT1", 0.00013666666666667)))) * 3600.0
        return phys_x, phys_y, pix_arcsec


def image_pixel_scale_arcsec(image_path: Path) -> float:
    with fits.open(image_path) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        return abs(float(hdu.header.get("CDELT2", hdu.header.get("CDELT1", 0.00013666666666667)))) * 3600.0


def load_point_source_masks(
    cluster_dir: Path,
    source_file: str | None,
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    max_radius_r500: float,
    sigma_min: float,
    radius_scale: float,
    min_radius_pix: float,
    skip_center_r500: float,
) -> list[PointSourceMask]:
    """Load wavdetect point-source masks from CIAO src.fits-like products."""
    if not source_file:
        return []
    path = Path(source_file)
    if not path.is_absolute():
        path = cluster_dir / path
    if not path.exists():
        print(f"[warn] Point-source file {path} not found; no point-source masks applied.")
        return []

    # src.fits radii are in Chandra sky pixels; use the merged-counts scale if available.
    pix_arcsec = 0.492
    counts_img = cluster_dir / "merged_counts.img"
    if counts_img.exists():
        pix_arcsec = image_pixel_scale_arcsec(counts_img)

    center = SkyCoord(ra=center_ra * u.deg, dec=center_dec * u.deg)
    masks: list[PointSourceMask] = []
    with fits.open(path) as hdul:
        data = hdul[1].data
        names = set(data.names)
        required = {"RA", "DEC", "SRC_SIGNIFICANCE", "R"}
        if not required.issubset(names):
            print(f"[warn] {path} is missing required columns {sorted(required - names)}; no point-source masks applied.")
            return []
        for row in data:
            sig = float(row["SRC_SIGNIFICANCE"])
            if sig < sigma_min:
                continue
            ra = float(row["RA"])
            dec = float(row["DEC"])
            src = SkyCoord(ra=ra * u.deg, dec=dec * u.deg)
            sep_arcsec = float(center.separation(src).to_value(u.arcsec))
            if sep_arcsec < skip_center_r500 * r500_arcsec:
                continue
            if sep_arcsec > max_radius_r500 * r500_arcsec:
                continue
            radii = np.asarray(row["R"], dtype=float)
            radius_pix = max(float(np.nanmax(radii)) * radius_scale, min_radius_pix)
            masks.append(
                PointSourceMask(
                    ra=ra,
                    dec=dec,
                    radius_arcsec=radius_pix * pix_arcsec,
                    significance=sig,
                    net_counts=float(row["NET_COUNTS"]) if "NET_COUNTS" in names else float("nan"),
                    separation_arcsec=sep_arcsec,
                )
            )
    return masks


def sky_xy_from_event_wcs(evt_path: Path, ra: float, dec: float) -> tuple[float, float, float]:
    """Return physical Chandra sky x/y for one event file.

    CIAO spectral tools are most reliable when the region for
    ``[sky=region(...)]`` is expressed in that event file's physical sky
    coordinates, not as a shared FK5 region reused across ObsIDs.
    """
    with fits.open(evt_path) as hdul:
        header = hdul[1].header
        wcs_header = fits.Header()
        wcs_header["NAXIS"] = 2
        wcs_header["CTYPE1"] = header["TCTYP11"]
        wcs_header["CTYPE2"] = header["TCTYP12"]
        wcs_header["CRVAL1"] = header["TCRVL11"]
        wcs_header["CRVAL2"] = header["TCRVL12"]
        wcs_header["CRPIX1"] = header["TCRPX11"]
        wcs_header["CRPIX2"] = header["TCRPX12"]
        wcs_header["CDELT1"] = header["TCDLT11"]
        wcs_header["CDELT2"] = header["TCDLT12"]
        wcs_header["CUNIT1"] = "deg"
        wcs_header["CUNIT2"] = "deg"
        wcs = WCS(wcs_header)
        x0, y0 = wcs.world_to_pixel(SkyCoord(ra=ra * u.deg, dec=dec * u.deg))
        pix_arcsec = abs(float(header["TCDLT12"])) * 3600.0
        # Astropy returns 0-based pixel coordinates; CIAO physical sky coords
        # use the FITS 1-based convention.
        return float(x0) + 1.0, float(y0) + 1.0, pix_arcsec


def count_events_in_xy_annulus(
    evt_path: Path,
    center_x: float,
    center_y: float,
    pix_arcsec: float,
    outer_arcsec: float,
    emin: float,
    emax: float,
    inner_arcsec: float = 0.0,
    exclude_circles: list[tuple[float, float, float]] | None = None,
) -> int | None:
    if not evt_path.exists():
        return None
    with fits.open(evt_path, memmap=True) as hdul:
        events = hdul[1].data
        names = {n.upper(): n for n in events.names}
        if "X" not in names or "Y" not in names:
            return None
        xs = np.asarray(events[names["X"]], dtype=float)
        ys = np.asarray(events[names["Y"]], dtype=float)
        energy_mask = np.ones(xs.shape, dtype=bool)
        if "ENERGY" in names:
            en = np.asarray(events[names["ENERGY"]], dtype=float) / 1000.0
            energy_mask = (en >= emin) & (en <= emax)
        radius_arcsec = np.hypot(xs - center_x, ys - center_y) * pix_arcsec
        mask = (radius_arcsec <= outer_arcsec) & (radius_arcsec >= inner_arcsec) & energy_mask
        for ex, ey, er_pix in exclude_circles or []:
            mask &= np.hypot(xs - ex, ys - ey) > er_pix
        return int(np.count_nonzero(mask))


def write_region(path: Path, ra: float, dec: float, radius_arcsec: float, annulus_inner: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Region file format: DS9 version 4.1\n")
        f.write("global color=green dashlist=8 3 width=2 font='helvetica 10 normal roman' select=1 highlite=1\n")
        f.write("fk5\n")
        if annulus_inner is None:
            f.write(f"circle({ra:.8f},{dec:.8f},{radius_arcsec:.3f}\")\n")
        else:
            f.write(f"annulus({ra:.8f},{dec:.8f},{annulus_inner:.3f}\",{radius_arcsec:.3f}\")\n")


def write_physical_sky_region(path: Path, x: float, y: float, radius_pix: float, annulus_inner_pix: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Region file format: CIAO version 1.0\n")
        f.write("physical\n")
        if annulus_inner_pix is None:
            f.write(f"circle({x:.6f},{y:.6f},{radius_pix:.6f})\n")
        else:
            f.write(f"annulus({x:.6f},{y:.6f},{annulus_inner_pix:.6f},{radius_pix:.6f})\n")


def write_aperture_overlay_plot(
    image_path: Path | None,
    out_plot: Path,
    ra: float,
    dec: float,
    r500_arcsec: float,
    bkg_inner_r500: float,
    bkg_outer_r500: float,
    source_inner_r500: float,
    point_source_masks: list[PointSourceMask],
    title: str,
) -> Path | None:
    """Plot the spectral source/background apertures on the cluster image."""
    if image_path is None or not image_path.exists():
        return None

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    with fits.open(image_path) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        data = np.asarray(hdu.data, dtype=float)
        wcs = WCS(hdu.header)
        x0, y0 = wcs.world_to_pixel(SkyCoord(ra=ra * u.deg, dec=dec * u.deg))
        pix_arcsec = abs(float(hdu.header.get("CDELT2", hdu.header.get("CDELT1", 0.00013666666666667)))) * 3600.0

    r500_pix = r500_arcsec / pix_arcsec
    bkg_inner_pix = bkg_inner_r500 * r500_pix
    bkg_outer_pix = bkg_outer_r500 * r500_pix
    source_inner_pix = source_inner_r500 * r500_pix

    pad = max(40.0, bkg_outer_pix * 1.08)
    ny, nx = data.shape
    xmin = max(0, int(math.floor(x0 - pad)))
    xmax = min(nx, int(math.ceil(x0 + pad)))
    ymin = max(0, int(math.floor(y0 - pad)))
    ymax = min(ny, int(math.ceil(y0 + pad)))
    crop = data[ymin:ymax, xmin:xmax]
    finite = crop[np.isfinite(crop) & (crop > 0)]
    if finite.size:
        vmin, vmax = np.nanpercentile(finite, [0.2, 99.4])
        clipped = np.clip(crop, vmin, vmax)
        show = np.sqrt(clipped - vmin + 1.0e-30)
    else:
        show = crop

    fig, ax = plt.subplots(figsize=(7.2, 7.0))
    ax.imshow(show, origin="lower", cmap="magma", extent=(xmin, xmax, ymin, ymax), interpolation="nearest")
    contour_data = np.asarray(show, dtype=float)
    contour_finite = contour_data[np.isfinite(contour_data)]
    if contour_finite.size and np.nanmax(contour_finite) > np.nanmin(contour_finite):
        levels = np.nanpercentile(contour_finite, [55, 70, 85, 95])
        levels = np.unique(levels)
        if levels.size > 1:
            ax.contour(
                np.linspace(xmin, xmax, contour_data.shape[1]),
                np.linspace(ymin, ymax, contour_data.shape[0]),
                contour_data,
                levels=levels,
                colors="white",
                linewidths=0.45,
                alpha=0.35,
            )
    ax.add_patch(Circle((x0, y0), r500_pix, fill=False, ec="cyan", lw=2.0, label="source outer R500"))
    if source_inner_r500 > 0:
        ax.add_patch(
            Circle((x0, y0), source_inner_pix, fill=False, ec="white", lw=2.0, ls="-", label=f"masked core {source_inner_r500:.2f}R500")
        )
    ax.add_patch(Circle((x0, y0), bkg_inner_pix, fill=False, ec="lime", lw=1.6, ls="--", label=f"background inner {bkg_inner_r500:.1f}R500"))
    ax.add_patch(Circle((x0, y0), bkg_outer_pix, fill=False, ec="lime", lw=1.6, ls="-.", label=f"background outer {bkg_outer_r500:.1f}R500"))
    for idx, src in enumerate(point_source_masks):
        sx, sy = wcs.world_to_pixel(SkyCoord(ra=src.ra * u.deg, dec=src.dec * u.deg))
        ax.add_patch(
            Circle(
                (float(sx), float(sy)),
                src.radius_arcsec / pix_arcsec,
                fill=False,
                ec="red",
                lw=1.1,
                alpha=0.9,
                label="masked point sources" if idx == 0 else None,
            )
        )
    ax.plot([x0], [y0], marker="+", ms=12, mew=2, color="white", label="cluster center")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Image X pixel")
    ax.set_ylabel("Image Y pixel")
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=8, framealpha=0.85)
    ax.text(
        0.02,
        0.02,
        f"R500 = {r500_arcsec:.1f} arcsec",
        transform=ax.transAxes,
        color="white",
        fontsize=10,
        bbox={"facecolor": "black", "alpha": 0.55, "edgecolor": "none"},
    )
    out_plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_plot, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out_plot


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), check=True)


def discover_individual_evt2(cluster_dir: Path) -> list[Path]:
    """Find per-ObsID reprocessed event files for spectral extraction."""
    patterns = [
        "raw/*/repro/*_repro_evt2.fits",
        "raw/*/repro/*repro_evt2.fits",
    ]
    evt_paths: list[Path] = []
    for pattern in patterns:
        evt_paths.extend(cluster_dir.glob(pattern))
    return sorted(set(p.resolve() for p in evt_paths))


def obsid_from_evt_path(evt: Path) -> str:
    parts = evt.parts
    if "raw" in parts:
        idx = parts.index("raw")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    stem = evt.stem
    digits = "".join(ch for ch in stem if ch.isdigit())
    return digits or stem


def run_specextract_one(cluster_dir: Path, evt: Path, src_region: str, bkg_region: str, outroot: Path) -> Path | None:
    if shutil.which("specextract") is None:
        print("[warn] CIAO specextract not found on PATH; skipping spectral extraction.")
        return None
    cmd = [
        "specextract",
        f"infile={evt}[sky={src_region}]",
        f"bkgfile={evt}[sky={bkg_region}]",
        f"outroot={outroot}",
        f"correctpsf={DEFAULT_SPECEXTRACT_CORRECTPSF}",
        f"weight={DEFAULT_SPECEXTRACT_WEIGHT}",
        f"bkgresp={DEFAULT_SPECEXTRACT_BKGRESP}",
        "clobber=yes",
    ]
    try:
        run(cmd, cwd=cluster_dir)
    except subprocess.CalledProcessError as exc:
        print(f"[warn] specextract failed for {evt}: {exc}")
        return None
    pi = Path(str(outroot) + ".pi")
    return pi if pi.exists() else None


def source_masks_for_event(evt: Path, masks: list[PointSourceMask]) -> list[tuple[float, float, float]]:
    circles: list[tuple[float, float, float]] = []
    for src in masks:
        x, y, pix_arcsec = sky_xy_from_event_wcs(evt, src.ra, src.dec)
        circles.append((x, y, src.radius_arcsec / pix_arcsec))
    return circles


def apply_region_exclusions(region: str, exclude_circles: list[tuple[float, float, float]]) -> str:
    for x, y, r in exclude_circles:
        region += f"-circle({x:.6f},{y:.6f},{r:.6f})"
    return region


def run_specextract_individual(
    cluster_dir: Path,
    evt_paths: list[Path],
    outdir: Path,
    name: str,
    product_tag: str,
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    source_inner_r500: float,
    bkg_inner_r500: float,
    bkg_outer_r500: float,
    energy_min: float,
    energy_max: float,
    point_source_masks: list[PointSourceMask],
) -> list[Path]:
    spectra: list[Path] = []
    if shutil.which("specextract") is None:
        print("[warn] CIAO specextract not found on PATH; skipping spectral extraction.")
        return spectra
    for evt in evt_paths:
        obsid = obsid_from_evt_path(evt)
        outroot = outdir / f"{name}_obs{obsid}_{product_tag}"
        x, y, pix_arcsec = sky_xy_from_event_wcs(evt, center_ra, center_dec)
        src_radius_pix = r500_arcsec / pix_arcsec
        src_inner_pix = source_inner_r500 * src_radius_pix
        bkg_inner_pix = bkg_inner_r500 * src_radius_pix
        bkg_outer_pix = bkg_outer_r500 * src_radius_pix
        reg_dir = outdir / "per_obs_regions"
        src_reg = reg_dir / f"{name}_obs{obsid}_{product_tag}_src_sky.reg"
        bkg_reg = reg_dir / f"{name}_obs{obsid}_{product_tag}_bkg_sky.reg"
        write_physical_sky_region(src_reg, x, y, src_radius_pix, src_inner_pix if source_inner_r500 > 0 else None)
        write_physical_sky_region(bkg_reg, x, y, bkg_outer_pix, bkg_inner_pix)
        exclude_circles = source_masks_for_event(evt, point_source_masks)
        if source_inner_r500 > 0:
            src_region = f"annulus({x:.6f},{y:.6f},{src_inner_pix:.6f},{src_radius_pix:.6f})"
        else:
            src_region = f"circle({x:.6f},{y:.6f},{src_radius_pix:.6f})"
        bkg_region = f"annulus({x:.6f},{y:.6f},{bkg_inner_pix:.6f},{bkg_outer_pix:.6f})"
        src_region = apply_region_exclusions(src_region, exclude_circles)
        bkg_region = apply_region_exclusions(bkg_region, exclude_circles)
        nsrc = count_events_in_xy_annulus(
            evt,
            x,
            y,
            pix_arcsec,
            r500_arcsec,
            energy_min,
            energy_max,
            source_inner_r500 * r500_arcsec,
            exclude_circles,
        )
        nbkg = count_events_in_xy_annulus(
            evt,
            x,
            y,
            pix_arcsec,
            bkg_outer_r500 * r500_arcsec,
            energy_min,
            energy_max,
            bkg_inner_r500 * r500_arcsec,
            exclude_circles,
        )
        print(f"[info] ObsID {obsid}: physical center=({x:.2f},{y:.2f}), src_counts={nsrc}, bkg_counts={nbkg}")
        if not nsrc:
            print(f"[warn] ObsID {obsid} source region has zero quick-look counts; skipping specextract for this ObsID.")
            continue
        pi = run_specextract_one(cluster_dir, evt, src_region, bkg_region, outroot)
        if pi is not None:
            spectra.append(pi)
    return spectra


def existing_individual_spectra(outdir: Path, name: str, product_tag: str) -> list[Path]:
    return sorted(outdir.glob(f"{name}_obs*_{product_tag}.pi"))


def write_sherpa_script(
    path: Path,
    spectrum_pis: list[Path],
    z: float,
    nh_1e22: float,
    out_json: Path,
    out_plot: Path,
    background_mode: str,
    energy_min: float = 0.5,
    energy_max: float = 7.0,
    kt_init: float = 7.0,
    fit_method: str = "levmar",
    fit_soft_bg: bool = False,
    m500_msun: float | None = None,
) -> None:
    spectra_literal = "[" + ", ".join(repr(str(p)) for p in spectrum_pis) + "]"
    soft_bg_setup = ""
    soft_bg_model = ""
    if fit_soft_bg:
        soft_bg_setup = """
bg_soft = xsapec.bg_soft
bg_soft.kT = 0.5
bg_soft.kT.freeze()
bg_soft.redshift = 0.0
bg_soft.redshift.freeze()
bg_soft.Abundanc = 1.0
bg_soft.norm = 1e-7
"""
        soft_bg_model = " * bg_soft"

    path.write_text(
        f'''#!/usr/bin/env sherpa
"""Jointly fit per-exposure R500 spectra with absorbed APEC in Sherpa.

Run inside a CIAO/Sherpa environment:
  sherpa {path.name}

Important: spectra are loaded per ObsID so each spectrum keeps its own ARF/RMF.
Do not replace these with a spectrum extracted from the merged event file.
"""
from sherpa.astro.ui import *
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

spectra = {spectra_literal}
background_mode = "{background_mode}"
if not spectra:
    raise SystemExit("No per-exposure spectra were provided to the Sherpa script.")

if background_mode == "wstat":
    set_stat("wstat")
else:
    set_stat("chi2gehrels")
set_method("{fit_method}")

# Shared physical model. The same kT, abundance, redshift, and nH are fitted
# against every exposure, while each data set keeps its own ARF/RMF response.
gal = xsphabs.gal
icm = xsapec.icm
gal.nH = {nh_1e22:.6g}
gal.nH.freeze()
icm.redshift = {z:.8g}
icm.redshift.freeze()
icm.kT = {kt_init:.4g}
icm.Abundanc = 0.3
icm.norm = 1e-3
{soft_bg_setup}

for i, pha in enumerate(spectra, start=1):
    load_pha(i, pha)
    try:
        ignore_bad()
    except Exception:
        pass
    notice_id(i, {energy_min}, {energy_max})
    if background_mode == "wstat":
        group_counts(1, i)
    else:
        group_counts(25, i)
    if background_mode == "subtract":
        subtract(i)
    set_source(i, gal * icm{soft_bg_model})

fit()
conf_results = None
try:
    conf()
    conf_results = get_conf_results()
except Exception as exc:
    print("[warn] conf() failed:", exc)

residual_summaries = []
fig, (ax, rax) = plt.subplots(
    2,
    1,
    figsize=(8.0, 6.2),
    sharex=True,
    gridspec_kw={{"height_ratios": [3.0, 1.0], "hspace": 0.05}},
)
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, pha in enumerate(spectra, start=1):
    label = pha.rsplit("/", 1)[-1].replace("_r500.pi", "")
    color = colors[(i - 1) % len(colors)]
    data_plot = get_data_plot(i)
    model_plot = get_model_plot(i)
    resid_plot = get_resid_plot(i)
    finite_resid = np.asarray(resid_plot.y, dtype=float)
    finite_resid = finite_resid[np.isfinite(finite_resid)]
    residual_summary = {{
        "dataset_id": i,
        "spectrum": pha,
        "n_bins": int(finite_resid.size),
        "mean_residual": float(np.mean(finite_resid)) if finite_resid.size else None,
        "median_residual": float(np.median(finite_resid)) if finite_resid.size else None,
        "rms_residual": float(np.sqrt(np.mean(finite_resid * finite_resid))) if finite_resid.size else None,
        "max_abs_residual": float(np.max(np.abs(finite_resid))) if finite_resid.size else None,
    }}
    residual_summaries.append(residual_summary)
    ax.errorbar(
        data_plot.x,
        data_plot.y,
        yerr=getattr(data_plot, "yerr", None),
        fmt="o",
        ms=3,
        lw=0.8,
        color=color,
        alpha=0.75,
        label=f"{{label}} data",
    )
    ax.plot(model_plot.x, model_plot.y, color=color, lw=1.6, label=f"{{label}} model")
    rax.axhline(0.0, color="0.25", lw=0.8, ls="--")
    rax.errorbar(
        resid_plot.x,
        resid_plot.y,
        yerr=getattr(resid_plot, "yerr", None),
        fmt="o",
        ms=3,
        lw=0.8,
        color=color,
        alpha=0.75,
    )

ax.set_yscale("log")
ax.set_ylabel("Counts s$^{{-1}}$ keV$^{{-1}}$")
rax.set_xlabel("Energy (keV)")
rax.set_ylabel("Residual")
ax.set_title("Joint absorbed APEC fit inside R500")
ax.legend(fontsize=7, ncol=2)
ax.grid(alpha=0.2)
rax.grid(alpha=0.2)
fig.savefig("{out_plot}", dpi=180, bbox_inches="tight")
plt.close(fig)

fr = get_fit_results()
rstat_raw = getattr(fr, "rstat", None)
rstat = None if rstat_raw is None else float(rstat_raw)
q_value = getattr(fr, "qval", None)
if q_value is not None:
    q_value = float(q_value)
if rstat is None:
    fit_quality = "no_reduced_statistic_for_this_statistic"
elif 0.8 <= rstat <= 1.2:
    fit_quality = "acceptable_reduced_statistic"
elif rstat < 0.8:
    fit_quality = "low_reduced_statistic_check_grouping_or_errors"
else:
    fit_quality = "high_reduced_statistic_check_model_background_or_calibration"

confidence_intervals = {{}}
if conf_results is not None:
    parnames = list(getattr(conf_results, "parnames", []) or [])
    parvals = list(getattr(conf_results, "parvals", []) or [])
    parmins = list(getattr(conf_results, "parmins", []) or [])
    parmaxes = list(getattr(conf_results, "parmaxes", []) or [])
    for pname, pval, pmin, pmax in zip(parnames, parvals, parmins, parmaxes):
        confidence_intervals[str(pname)] = {{
            "best": None if pval is None else float(pval),
            "lower_delta_1sigma": None if pmin is None else float(pmin),
            "upper_delta_1sigma": None if pmax is None else float(pmax),
        }}

vals = {{
    "n_spectra": len(spectra),
    "spectra": spectra,
    "sherpa_background_mode": background_mode,
    "temperature_keV": float(icm.kT.val),
    "abundance_solar": float(icm.Abundanc.val),
    "apec_norm": float(icm.norm.val),
    "nH_1e22_cm2": float(gal.nH.val),
    "redshift": float(icm.redshift.val),
    "statname": fr.statname,
    "statval": float(fr.statval),
    "dof": int(fr.dof),
    "q_value": q_value,
    "rstat": rstat,
    "fit_quality_flag": fit_quality,
    "confidence_intervals": confidence_intervals,
    "residual_summaries": residual_summaries,
    "diagnostic_checks": {{
        "energy_band_keV": [{energy_min}, {energy_max}],
        "model": "xsphabs * xsapec",
        "background_treatment": "WSTAT non-subtractive source+background likelihood" if background_mode == "wstat" else "background-subtracted chi-square comparison mode",
        "fit_strategy": "joint fit to individual exposure spectra; each spectrum keeps its own ARF/RMF",
        "visual_check": "inspect data/model agreement and residuals in fit_plot_png",
        "reduced_statistic_rule_of_thumb": "near 1 is usually acceptable; much below 1 can indicate conservative errors or grouping; much above 1 suggests model/background/calibration issues",
        "background_check": "look for systematic high-energy residuals where particle/background mismatch is common",
        "line_check": "for Fe-K, compare residuals near observed 6.7/(1+z) keV",
    }},
    "fit_plot_png": "{out_plot}",
}}
with open("{out_json}", "w") as f:
    json.dump(vals, f, indent=2, sort_keys=True)
print(json.dumps(vals, indent=2, sort_keys=True))
'''
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("cluster_dir", type=Path, nargs="?", help="Processed cluster directory; defaults to DEFAULT_CLUSTER_DIR")
    parser.add_argument("--cluster", default=None, help="Cluster config key/name/alias; defaults to DEFAULT_CLUSTER_KEY in this script")
    parser.add_argument("--cluster-table", type=Path, default=CLUSTER_TABLE_PATH, help="CSV table containing cluster centers and parameters")
    parser.add_argument("--list-clusters", action="store_true", help="Print configured clusters and exit")
    parser.add_argument("--name", default=None, help="Output label; defaults to the configured cluster key")
    parser.add_argument("--z", type=float, default=None, help="Cluster redshift; overrides config")
    parser.add_argument("--m500", type=float, default=None, help="Independent M500 value; overrides config")
    parser.add_argument("--m500-h-inverse", action="store_true", help="Interpret --m500 as h^-1 Msun and convert to Msun")
    parser.add_argument("--h0", type=float, default=None, help="H0 in km/s/Mpc; overrides config")
    parser.add_argument("--omega-m", type=float, default=None, help="Matter density; overrides config")
    parser.add_argument("--center-mode", choices=("catalog", "xray_peak", "manual"), default=DEFAULT_CENTER_MODE, help="How to choose the aperture/fitting center")
    parser.add_argument("--xray-peak-search-arcsec", type=float, default=DEFAULT_XRAY_PEAK_SEARCH_ARCSEC, help="Search radius around the seed center for --center-mode xray_peak")
    parser.add_argument("--center-ra", type=float, default=None, help="Cluster center RA in degrees; overrides config")
    parser.add_argument("--center-dec", type=float, default=None, help="Cluster center Dec in degrees; overrides config")
    parser.add_argument("--nh", type=float, default=None, help="Galactic nH in units of 1e22 cm^-2; overrides config")
    parser.add_argument("--flux-image", default=DEFAULT_FLUX_IMAGE, help="Flux image relative to cluster_dir or absolute path")
    parser.add_argument("--aperture-plot-image", default=DEFAULT_APERTURE_PLOT_IMAGE, help="Image used for the aperture overlay plot, relative to cluster_dir or absolute path")
    parser.add_argument("--evt", default=DEFAULT_MERGED_EVT, help="Merged event file used only for quick-look counts")
    parser.add_argument("--mask-point-sources", action=argparse.BooleanOptionalAction, default=DEFAULT_MASK_POINT_SOURCES, help="Exclude wavdetect point sources from source/background regions")
    parser.add_argument("--point-source-file", default=DEFAULT_POINT_SOURCE_FILE, help="CIAO wavdetect source table, relative to cluster_dir unless absolute")
    parser.add_argument("--point-source-sigma-min", type=float, default=DEFAULT_POINT_SOURCE_SIGMA_MIN, help="Minimum wavdetect source significance to mask")
    parser.add_argument("--point-source-radius-scale", type=float, default=DEFAULT_POINT_SOURCE_RADIUS_SCALE, help="Multiplier applied to wavdetect source radii")
    parser.add_argument("--point-source-min-radius-pix", type=float, default=DEFAULT_POINT_SOURCE_MIN_RADIUS_PIX, help="Minimum point-source mask radius in Chandra sky pixels")
    parser.add_argument("--point-source-skip-center-r500", type=float, default=DEFAULT_POINT_SOURCE_SKIP_CENTER_R500, help="Do not mask wavdetect detections this close to the cluster center")
    parser.add_argument(
        "--individual-evt-glob",
        default=DEFAULT_INDIVIDUAL_EVT_GLOB,
        help="Optional glob, relative to cluster_dir, for per-exposure evt2 files used by specextract",
    )
    parser.add_argument("--energy-min", type=float, default=DEFAULT_ENERGY_MIN_KEV, help="Count/luminosity diagnostic band lower edge, keV")
    parser.add_argument("--energy-max", type=float, default=DEFAULT_ENERGY_MAX_KEV, help="Count diagnostic band upper edge, keV")
    parser.add_argument("--bkg-inner-r500", type=float, default=DEFAULT_BKG_INNER_R500, help="Background annulus inner radius in R500")
    parser.add_argument("--bkg-outer-r500", type=float, default=DEFAULT_BKG_OUTER_R500, help="Background annulus outer radius in R500")
    parser.add_argument("--excise-core", action=argparse.BooleanOptionalAction, default=DEFAULT_EXCISE_CORE, help="Mask the central core from the spectral source aperture")
    parser.add_argument("--core-inner-r500", type=float, default=DEFAULT_CORE_INNER_R500, help="Core radius to mask, in units of R500, when --excise-core is enabled")
    parser.add_argument("--sherpa-background-mode", choices=("wstat", "subtract"), default=DEFAULT_SHERPA_BACKGROUND_MODE, help="Sherpa background treatment for the spectral fit")
    parser.add_argument("--run-specextract", action=argparse.BooleanOptionalAction, default=DEFAULT_RUN_SPECEXTRACT, help="Run CIAO specextract if available")
    parser.add_argument("--run-sherpa", action=argparse.BooleanOptionalAction, default=DEFAULT_RUN_SHERPA, help="Run Sherpa fit script if available and spectrum exists")
    parser.add_argument("--fit-method", default="levmar", help="Sherpa optimization method: levmar, neldermead, or moncar")
    parser.add_argument("--fit-soft-bg", action="store_true", help="Add a 0.5 keV soft thermal background component to the fit model")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configs = load_cluster_configs_from_table(args.cluster_table)
    if args.list_clusters:
        for key, cfg in configs.items():
            z = "" if cfg.redshift is None else f"{cfg.redshift:g}"
            m = "" if cfg.m500 is None else f"{cfg.m500:.6g}"
            print(f"{key},{cfg.name},{cfg.center_ra:.8f},{cfg.center_dec:.8f},{z},{m},{' '.join(cfg.obsids)}")
        return

    requested_cluster = args.cluster or DEFAULT_CLUSTER_KEY
    config_key, config = resolve_cluster_config(requested_cluster, configs)
    cluster_dir = args.cluster_dir or default_cluster_dir(config_key, config)
    if cluster_dir is None:
        raise SystemExit(f"No data directory found for {config_key}. Pass one explicitly as the positional cluster_dir.")
    cluster_dir = cluster_dir.resolve()
    outdir = cluster_dir / "postprocess_r500"
    outdir.mkdir(exist_ok=True)

    name = args.name or config_key
    redshift = args.z if args.z is not None else config.redshift
    m500 = args.m500 if args.m500 is not None else config.m500
    m500_h_inverse = args.m500_h_inverse or (args.m500 is None and config.m500_h_inverse)
    h0 = args.h0 if args.h0 is not None else config.h0
    omega_m = args.omega_m if args.omega_m is not None else config.omega_m
    catalog_center_ra = config.center_ra
    catalog_center_dec = config.center_dec
    nh = args.nh if args.nh is not None else config.nh_1e22

    if redshift is None or m500 is None:
        raise SystemExit(
            f"{config_key} has no configured redshift/M500 yet. "
            "Add them to CLUSTER_CONFIGS or pass --z and --m500."
        )

    h = h0 / 100.0
    m500_msun = m500 / h if m500_h_inverse else m500
    r500_mpc = compute_r500_mpc(m500_msun, redshift, h0, omega_m)
    r500_arcsec = angular_radius_arcsec(r500_mpc, redshift, h0, omega_m)
    source_inner_r500 = args.core_inner_r500 if args.excise_core else 0.0
    source_inner_arcsec = source_inner_r500 * r500_arcsec
    aperture_tag = "r500_coreexcised" if source_inner_r500 > 0 else "r500"
    flux_image = choose_flux_image(cluster_dir, args.flux_image)
    aperture_plot_image = choose_aperture_plot_image(cluster_dir, flux_image, args.aperture_plot_image)
    center_ra, center_dec, center_offset_arcsec, actual_center_mode = resolve_analysis_center(
        args.center_mode,
        catalog_center_ra,
        catalog_center_dec,
        args.center_ra,
        args.center_dec,
        aperture_plot_image or flux_image,
        args.xray_peak_search_arcsec,
    )
    center_tag = "".join(ch if ch.isalnum() else "_" for ch in actual_center_mode).strip("_")
    point_source_masks = (
        load_point_source_masks(
            cluster_dir,
            args.point_source_file,
            center_ra,
            center_dec,
            r500_arcsec,
            args.bkg_outer_r500,
            args.point_source_sigma_min,
            args.point_source_radius_scale,
            args.point_source_min_radius_pix,
            args.point_source_skip_center_r500,
        )
        if args.mask_point_sources
        else []
    )
    product_tag = f"{aperture_tag}_{center_tag}"
    if point_source_masks:
        product_tag += "_psmask"

    src_reg = outdir / f"{name}_{product_tag}_src.reg"
    bkg_reg = outdir / f"{name}_{product_tag}_bkg.reg"
    write_region(src_reg, center_ra, center_dec, r500_arcsec, source_inner_arcsec if source_inner_r500 > 0 else None)
    write_region(bkg_reg, center_ra, center_dec, args.bkg_outer_r500 * r500_arcsec, args.bkg_inner_r500 * r500_arcsec)

    aperture_flux = None
    aperture_flux_note = None
    aperture_luminosity = None
    aperture_plot = None
    if flux_image and flux_image.exists():
        aperture_flux, aperture_flux_note = image_sum_in_sky_annulus(
            flux_image,
            center_ra,
            center_dec,
            r500_arcsec,
            source_inner_arcsec,
            point_source_masks,
        )
        dl_cm = luminosity_distance_cm(redshift, h0, omega_m)
        aperture_luminosity = 4.0 * math.pi * dl_cm * dl_cm * aperture_flux
        aperture_plot = write_aperture_overlay_plot(
            aperture_plot_image,
            outdir / f"{name}_{product_tag}_aperture_overlay.png",
            center_ra,
            center_dec,
            r500_arcsec,
            args.bkg_inner_r500,
            args.bkg_outer_r500,
            source_inner_r500,
            point_source_masks,
            f"{name} spectral aperture on cluster image",
        )
    else:
        print("[warn] No flux image found; luminosity from image skipped.")

    evt = Path(args.evt)
    if not evt.is_absolute():
        evt = cluster_dir / evt
    net_counts = None
    bkg_counts = None
    if flux_image and flux_image.exists():
        center_x, center_y, pix_arcsec = sky_xy_from_image_wcs(flux_image, center_ra, center_dec)
        net_counts = count_events_in_xy_annulus(
            evt,
            center_x,
            center_y,
            pix_arcsec,
            r500_arcsec,
            args.energy_min,
            args.energy_max,
            source_inner_arcsec,
            [],
        )
        bkg_counts = count_events_in_xy_annulus(
            evt,
            center_x,
            center_y,
            pix_arcsec,
            args.bkg_outer_r500 * r500_arcsec,
            args.energy_min,
            args.energy_max,
            args.bkg_inner_r500 * r500_arcsec,
            [],
        )

    if args.individual_evt_glob and args.individual_evt_glob.strip().upper() != "AUTO":
        evt_paths = sorted(cluster_dir.glob(args.individual_evt_glob))
    else:
        evt_paths = discover_individual_evt2(cluster_dir)

    spectrum_pis: list[Path] = []
    if args.run_specextract:
        spectrum_pis = run_specextract_individual(
            cluster_dir,
            evt_paths,
            outdir,
            name,
            product_tag,
            center_ra,
            center_dec,
            r500_arcsec,
            source_inner_r500,
            args.bkg_inner_r500,
            args.bkg_outer_r500,
            args.energy_min,
            args.energy_max,
            point_source_masks,
        )

    if not spectrum_pis:
        spectrum_pis = existing_individual_spectra(outdir, name, product_tag)

    fit_tag = f"{product_tag}_{args.sherpa_background_mode}"
    sherpa_script = outdir / f"fit_{name}_{fit_tag}_sherpa.py"
    fit_json = outdir / f"{name}_{fit_tag}_fit_results.json"
    fit_plot = outdir / f"{name}_{fit_tag}_fit_plot.png"
    kt_init = 5.0 * (m500_msun / 3e14) ** (2.0 / 3.0) if m500_msun else 7.0
    write_sherpa_script(
        sherpa_script, spectrum_pis, redshift, nh, fit_json, fit_plot, args.sherpa_background_mode,
        energy_min=args.energy_min, energy_max=args.energy_max,
        kt_init=kt_init, fit_method=args.fit_method,
        fit_soft_bg=args.fit_soft_bg, m500_msun=m500_msun,
    )

    if args.run_sherpa and spectrum_pis:
        if shutil.which("sherpa") is None:
            print("[warn] sherpa not found on PATH; fit script written but not run.")
        else:
            run(["sherpa", str(sherpa_script)], cwd=outdir)
    elif args.run_sherpa and not spectrum_pis:
        print("[warn] No per-exposure spectra exist yet; Sherpa joint fit was not run.")

    result = ClusterResult(
        name=name,
        cluster_dir=str(cluster_dir),
        redshift=redshift,
        m500_msun=m500_msun,
        r500_mpc=r500_mpc,
        r500_arcsec=r500_arcsec,
        source_inner_r500=source_inner_r500,
        source_inner_arcsec=source_inner_arcsec,
        core_excised=source_inner_r500 > 0,
        center_mode=actual_center_mode,
        catalog_center_ra_deg=catalog_center_ra,
        catalog_center_dec_deg=catalog_center_dec,
        center_ra_deg=center_ra,
        center_dec_deg=center_dec,
        center_offset_from_catalog_arcsec=center_offset_arcsec,
        point_source_mask_file=str((cluster_dir / args.point_source_file).resolve()) if args.mask_point_sources and args.point_source_file else None,
        point_source_mask_count=len(point_source_masks),
        point_source_mask_sigma_min=args.point_source_sigma_min if args.mask_point_sources else None,
        flux_image=str(flux_image) if flux_image else None,
        aperture_plot_image=str(aperture_plot_image) if aperture_plot_image else None,
        aperture_flux_erg_s_cm2=aperture_flux,
        aperture_flux_note=aperture_flux_note,
        aperture_luminosity_erg_s=aperture_luminosity,
        net_counts_r500=net_counts,
        bkg_counts_region=bkg_counts,
        source_region=str(src_reg),
        background_region=str(bkg_reg),
        aperture_plot_png=str(aperture_plot) if aperture_plot else None,
        individual_event_files=[str(p) for p in evt_paths],
        spectrum_pis=[str(p) for p in spectrum_pis],
        sherpa_background_mode=args.sherpa_background_mode,
        sherpa_script=str(sherpa_script),
        fit_results_json=str(fit_json),
        fit_plot_png=str(fit_plot),
    )

    json_path = outdir / f"{name}_{product_tag}_summary.json"
    csv_path = outdir / f"{name}_{product_tag}_summary.csv"
    json_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(result).keys()))
        writer.writeheader()
        writer.writerow(asdict(result))

    table_path = args.cluster_table if args.cluster_table.is_absolute() else Path.cwd() / args.cluster_table
    point_source_path = None
    if args.mask_point_sources and args.point_source_file:
        point_source_path = Path(args.point_source_file)
        if not point_source_path.is_absolute():
            point_source_path = cluster_dir / point_source_path

    written_outputs = [
        ("summary JSON", json_path),
        ("summary CSV", csv_path),
        ("source region", src_reg),
        ("background region", bkg_reg),
        ("aperture layout X-ray image", aperture_plot),
        ("Sherpa script", sherpa_script),
        ("Sherpa fit results JSON", fit_json),
        ("Sherpa fit plot", fit_plot),
    ]
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    print("\nResolved path settings:")
    print(f"  working directory: {Path.cwd()}")
    print(f"  cluster table: {table_path.resolve()}")
    print(f"  cluster data directory: {cluster_dir}")
    print(f"  output directory: {outdir}")
    print(f"  flux image for luminosity: {flux_image if flux_image else 'not found'}")
    print(f"  image used for aperture overlay: {aperture_plot_image if aperture_plot_image else 'not found'}")
    print(f"  point-source table: {point_source_path if point_source_path else 'disabled'}")
    print(f"  individual evt2 glob: {args.individual_evt_glob}")
    print("\nFiles used:")
    print(f"  merged event file for imaging/count diagnostics: {evt}")
    if evt_paths:
        print("  individual event files for spectra:")
        for evt_path in evt_paths:
            print(f"    {evt_path}")
    else:
        print("  individual event files for spectra: none found")
    if spectrum_pis:
        print("  individual spectra loaded by Sherpa:")
        for spectrum_pi in spectrum_pis:
            print(f"    {spectrum_pi}")
    else:
        print("  individual spectra loaded by Sherpa: none found")
    print("\nWrote:")
    for label, output_path in written_outputs:
        if output_path is not None:
            print(f"  {label}: {output_path}")


if __name__ == "__main__":
    main()
