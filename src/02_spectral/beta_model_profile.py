#!/usr/bin/env python3
"""Extract radial surface brightness profile from flux image and fit β-model.

Computes the emission measure ratio R_EM between a background annulus and
the source region, used to constrain the ICM contribution in the annulus
during joint spectral fitting.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.optimize import curve_fit

sys.path.insert(0, str(Path(__file__).parent))
from postproces_cluster import (
    CLUSTER_TABLE_PATH,
    angular_radius_arcsec,
    compute_r500_mpc,
    default_cluster_dir,
    load_cluster_configs_from_table,
    resolve_cluster_config,
    sky_xy_from_image_wcs,
    image_pixel_scale_arcsec,
)


def beta_model(R: float | np.ndarray, S0: float, rc: float, beta: float, bg: float) -> float | np.ndarray:
    """β-model surface brightness profile."""
    return S0 * (1.0 + (R / rc) ** 2) ** (-3.0 * beta + 0.5) + bg


def extract_profile(
    image_path: Path,
    center_ra: float,
    center_dec: float,
    r_max_arcsec: float,
    n_bins: int = 25,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract azimuthally-averaged radial surface brightness profile.

    Returns: (r_mid_arcsec, S_mean, S_err) per annular bin.
    """
    from astropy.io import fits
    from astropy.wcs import WCS
    from astropy.coordinates import SkyCoord
    import astropy.units as u

    with fits.open(image_path) as hdul:
        data = hdul[0].data.astype(float)
        header = hdul[0].header

    w = WCS(header)
    px, py = w.world_to_pixel(SkyCoord(ra=center_ra * u.deg, dec=center_dec * u.deg))
    pix_arcsec = abs(header.get("CDELT2", 0.000136667)) * 3600.0

    ny, nx = data.shape
    yy, xx = np.mgrid[:ny, :nx]
    dist = np.sqrt((xx - px) ** 2 + (yy - py) ** 2) * pix_arcsec

    r_edges = np.linspace(0, r_max_arcsec, n_bins + 1)
    r_mid = 0.5 * (r_edges[:-1] + r_edges[1:])
    S_mean = np.zeros(n_bins)
    S_err = np.zeros(n_bins)

    for i in range(n_bins):
        mask = (dist >= r_edges[i]) & (dist < r_edges[i + 1])
        pix = data[mask]
        pix = pix[np.isfinite(pix)]
        if len(pix) > 0:
            S_mean[i] = np.mean(pix)
            S_err[i] = np.std(pix) / np.sqrt(len(pix)) if len(pix) > 1 else np.mean(pix) * 0.1
        else:
            S_mean[i] = 0.0
            S_err[i] = 1e-20

    return r_mid, S_mean, S_err


def fit_beta_model(
    r_arcsec: np.ndarray,
    S: np.ndarray,
    S_err: np.ndarray,
    r500_arcsec: float,
    bkg_inner_r500: float = 1.2,
    bkg_outer_r500: float = 1.8,
) -> dict:
    """Fit β-model to surface brightness profile.

    Returns dict with: S0, rc_arcsec, beta, bg, R_EM, popt, pcov, success.
    """
    r_norm = r_arcsec / r500_arcsec  # normalize to R500

    # Initial guesses
    S0_init = np.max(S) - np.median(S[-5:])
    rc_init = 0.1  # in units of R500
    beta_init = 0.67
    bg_init = np.median(S[-5:])

    # Only fit bins with positive signal
    good = S > 0
    r_fit = r_norm[good]
    S_fit = S[good]
    err_fit = np.clip(S_err[good], S_fit * 0.05, None)

    try:
        upper_bg = max(S0_init * 100, np.max(S) * 2)
        popt, pcov = curve_fit(
            beta_model,
            r_fit,
            S_fit,
            p0=[S0_init, rc_init, beta_init, bg_init],
            sigma=err_fit,
            absolute_sigma=True,
            bounds=(
                [0, 0.005, 0.2, -np.max(S)],
                [np.max(S) * 10, 2.0, 1.5, upper_bg],
            ),
            maxfev=10000,
        )
        success = True
    except RuntimeError:
        popt = [S0_init, rc_init, beta_init, bg_init]
        pcov = np.eye(4) * np.nan
        success = False

    S0, rc_R500, beta, bg = popt
    rc_arcsec = rc_R500 * r500_arcsec

    # Compute R_EM: emission measure ratio between annulus and source
    # R_EM = ∫_{1.2}^{1.8} S_model(R) × 2πR dR / ∫_{0}^{1} S_model(R) × 2πR dR
    # (all in units of R500)
    def integrand(R):
        return (beta_model(R, S0, rc_R500, beta, 0) - bg) * 2 * np.pi * R  # subtract bg, only ICM

    # Only integrate where model > bg (i.e., ICM signal exists)
    num, _ = quad(integrand, 1.2, 1.8, limit=100)
    den, _ = quad(integrand, 0.0, 1.0, limit=100)
    R_EM = max(num / den, 0) if den > 0 else 0

    # Fallback: direct measurement from observed profile
    # Use outermost 20% of bins as background estimate
    n_bg = max(3, len(r_arcsec) // 5)
    bg_est = np.mean(S[-n_bg:])
    r_norm_all = r_arcsec / r500_arcsec
    # Net emission in source region (0-1 R500)
    src_mask = r_norm_all <= 1.0
    src_net = np.sum((S[src_mask] - bg_est) * 2 * np.pi * r_arcsec[src_mask])  # proxy for ∫ S·2πR dR
    # Net emission in annulus (1.2-1.8 R500)
    ann_mask = (r_norm_all >= bkg_inner_r500) & (r_norm_all <= bkg_outer_r500)
    ann_net = np.sum((S[ann_mask] - bg_est) * 2 * np.pi * r_arcsec[ann_mask])
    R_EM_direct = max(ann_net / src_net, 0.001) if src_net > 0 else 0.01  # minimum 0.1%

    return {
        "S0": float(S0),
        "rc_R500": float(rc_R500),
        "rc_arcsec": float(rc_arcsec),
        "beta": float(beta),
        "bg": float(bg),
        "R_EM": float(R_EM),
        "R_EM_direct": float(R_EM_direct),
        "popt": [float(x) for x in popt],
        "success": success,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--cluster-table", type=Path, default=CLUSTER_TABLE_PATH)
    parser.add_argument("--h0", type=float, default=70.0)
    parser.add_argument("--omega-m", type=float, default=0.3)
    parser.add_argument("--n-bins", type=int, default=25)
    parser.add_argument("--bkg-inner-r500", type=float, default=1.2)
    parser.add_argument("--bkg-outer-r500", type=float, default=1.8)
    args = parser.parse_args()

    configs = load_cluster_configs_from_table(args.cluster_table)
    config_key, config = resolve_cluster_config(args.cluster, configs)
    cluster_dir = default_cluster_dir(config_key, config)
    if cluster_dir is None:
        raise SystemExit(f"No data directory for {config_key}")
    cluster_dir = cluster_dir.resolve()

    redshift = config.redshift
    m500_raw = config.m500
    if redshift is None or m500_raw is None:
        raise SystemExit(f"Need redshift and M500 for {config_key}")
    h = args.h0 / 100.0
    m500_msun = m500_raw / h if config.m500_h_inverse else m500_raw

    r500_mpc = compute_r500_mpc(m500_msun, redshift, args.h0, args.omega_m)
    r500_arcsec = angular_radius_arcsec(r500_mpc, redshift, args.h0, args.omega_m)

    flux_image = cluster_dir / "processed/clean_fluxed/flux_clean.img"
    if not flux_image.exists():
        raise SystemExit(f"Flux image not found: {flux_image}")

    print(f"[info] {config_key}: R500={r500_arcsec:.1f}\"")
    print(f"[info] Extracting profile from {flux_image.name} ...")

    r_mid, S, S_err = extract_profile(
        flux_image, config.center_ra, config.center_dec,
        r_max_arcsec=2.0 * r500_arcsec,
        n_bins=args.n_bins,
    )

    result = fit_beta_model(r_mid, S, S_err, r500_arcsec)

    print(f"[info] β-model fit: S0={result['S0']:.4e}, rc={result['rc_arcsec']:.1f}\", "
          f"β={result['beta']:.3f}, bg={result['bg']:.4e}")
    print(f"[info] R_EM = {result['R_EM']:.4f} "
          f"(ICM fraction in {args.bkg_inner_r500}-{args.bkg_outer_r500} R500 annulus)")

    # Save results
    outdir = cluster_dir / "postprocess_r500_blanksky"
    outdir.mkdir(exist_ok=True)
    out_json = outdir / f"{config_key}_beta_model.json"
    result["r500_arcsec"] = r500_arcsec
    result["cluster_key"] = config_key
    result["bkg_inner_r500"] = args.bkg_inner_r500
    result["bkg_outer_r500"] = args.bkg_outer_r500
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)
    print(f"[info] Saved: {out_json}")


if __name__ == "__main__":
    main()
