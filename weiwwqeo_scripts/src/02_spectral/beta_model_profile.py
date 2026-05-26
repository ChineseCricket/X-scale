#!/usr/bin/env python3
"""Radial surface-brightness profile and beta-model helper.

This module intentionally has no hard scipy dependency. If scipy is available it
uses curve_fit; otherwise it falls back to a small beta/rc grid with linear
least-squares amplitudes. The model is used to estimate the ICM emission-measure
leakage from a source aperture into an outer annulus.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
import astropy.units as u


@dataclass
class BetaProfileResult:
    image: str
    center_ra_deg: float
    center_dec_deg: float
    r500_arcsec: float
    nbins: int
    max_radius_r500: float
    radii_arcsec: list[float]
    sb: list[float]
    sb_err: list[float]
    area_arcsec2: list[float]
    s0: float
    rc_arcsec: float
    beta: float
    s_bg: float
    fit_method: str
    chi2: float
    dof: int
    r_em_annulus_to_source: float
    annulus_inner_r500: float
    annulus_outer_r500: float
    source_inner_r500: float
    source_outer_r500: float
    plot_png: str | None


def image_pixel_scale_arcsec(header: fits.Header) -> float:
    cdelt = header.get("CDELT2", header.get("CDELT1"))
    if cdelt is not None:
        return abs(float(cdelt)) * 3600.0
    cd11 = header.get("CD1_1")
    cd22 = header.get("CD2_2")
    if cd11 is not None and cd22 is not None:
        return math.sqrt(abs(float(cd11) * float(cd22))) * 3600.0
    return 0.492


def sky_xy_from_image_wcs(image: Path, ra: float, dec: float) -> tuple[float, float, float]:
    with fits.open(image) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        wcs = WCS(hdu.header)
        x, y = wcs.world_to_pixel(SkyCoord(ra=ra * u.deg, dec=dec * u.deg))
        return float(x), float(y), image_pixel_scale_arcsec(hdu.header)


def beta_component(r_arcsec: np.ndarray, s0: float, rc_arcsec: float, beta: float) -> np.ndarray:
    rc = max(float(rc_arcsec), 1.0e-6)
    return s0 * (1.0 + (r_arcsec / rc) ** 2) ** (-3.0 * beta + 0.5)


def beta_model(r_arcsec: np.ndarray, s0: float, rc_arcsec: float, beta: float, s_bg: float) -> np.ndarray:
    return beta_component(r_arcsec, s0, rc_arcsec, beta) + s_bg


def extract_radial_profile(
    image: Path,
    ra: float,
    dec: float,
    r500_arcsec: float,
    nbins: int = 20,
    max_radius_r500: float = 2.0,
) -> dict[str, np.ndarray]:
    with fits.open(image) as hdul:
        hdu = next(h for h in hdul if getattr(h, "data", None) is not None and h.data is not None)
        data = np.asarray(hdu.data, dtype=float)
        wcs = WCS(hdu.header)
        x0, y0 = wcs.world_to_pixel(SkyCoord(ra=ra * u.deg, dec=dec * u.deg))
        pix_arcsec = image_pixel_scale_arcsec(hdu.header)

    yy, xx = np.indices(data.shape, dtype=float)
    rr_arcsec = np.hypot(xx - float(x0), yy - float(y0)) * pix_arcsec
    edges = np.linspace(0.0, max_radius_r500 * r500_arcsec, nbins + 1)
    radii = 0.5 * (edges[:-1] + edges[1:])
    sb = np.full(nbins, np.nan)
    sb_err = np.full(nbins, np.nan)
    area = np.zeros(nbins)
    sums = np.zeros(nbins)
    npix = np.zeros(nbins, dtype=int)
    pix_area = pix_arcsec * pix_arcsec

    finite = np.isfinite(data)
    for i in range(nbins):
        mask = finite & (rr_arcsec >= edges[i]) & (rr_arcsec < edges[i + 1])
        vals = data[mask]
        npix[i] = vals.size
        area[i] = vals.size * pix_area
        if vals.size:
            sums[i] = float(np.nansum(vals))
            sb[i] = sums[i] / max(area[i], 1.0e-30)
            # Conservative empirical error; flux images are exposure corrected,
            # so pure Poisson errors are not directly available here.
            sb_err[i] = float(np.nanstd(vals) / math.sqrt(vals.size) / max(pix_area, 1.0e-30))
            if not np.isfinite(sb_err[i]) or sb_err[i] <= 0:
                sb_err[i] = max(abs(sb[i]), 1.0e-30) / math.sqrt(vals.size)

    return {"radii_arcsec": radii, "sb": sb, "sb_err": sb_err, "area_arcsec2": area, "sum": sums, "npix": npix}


def fit_beta_profile(r: np.ndarray, y: np.ndarray, yerr: np.ndarray, r500_arcsec: float) -> tuple[dict[str, float], str, float, int]:
    valid = np.isfinite(r) & np.isfinite(y) & np.isfinite(yerr) & (yerr > 0)
    r = r[valid]
    y = y[valid]
    yerr = yerr[valid]
    if r.size < 5:
        raise ValueError("Not enough valid profile bins for beta-model fitting")

    try:
        from scipy.optimize import curve_fit  # type: ignore

        p0 = [max(float(np.nanmax(y) - np.nanmin(y)), 1.0e-20), 0.1 * r500_arcsec, 0.67, max(float(np.nanmin(y)), 0.0)]
        bounds = ([0.0, 0.005 * r500_arcsec, 0.25, 0.0], [np.inf, 1.0 * r500_arcsec, 1.5, np.inf])
        popt, _ = curve_fit(beta_model, r, y, p0=p0, sigma=yerr, absolute_sigma=True, bounds=bounds, maxfev=20000)
        model = beta_model(r, *popt)
        chi2 = float(np.sum(((y - model) / yerr) ** 2))
        return {"s0": float(popt[0]), "rc_arcsec": float(popt[1]), "beta": float(popt[2]), "s_bg": float(popt[3])}, "scipy_curve_fit", chi2, max(int(r.size - 4), 0)
    except Exception:
        pass

    # Fallback: grid over rc and beta. For fixed shape f(r), solve y = s0*f + bg.
    best: tuple[float, float, float, float, float] | None = None
    weights = 1.0 / np.maximum(yerr, 1.0e-30)
    for rc in np.linspace(0.03 * r500_arcsec, 0.5 * r500_arcsec, 80):
        for beta in np.linspace(0.35, 1.15, 81):
            f = (1.0 + (r / rc) ** 2) ** (-3.0 * beta + 0.5)
            a = np.vstack([f, np.ones_like(f)]).T * weights[:, None]
            b = y * weights
            coeff, *_ = np.linalg.lstsq(a, b, rcond=None)
            s0 = max(float(coeff[0]), 0.0)
            bg = max(float(coeff[1]), 0.0)
            model = s0 * f + bg
            chi2 = float(np.sum(((y - model) / yerr) ** 2))
            if best is None or chi2 < best[0]:
                best = (chi2, s0, rc, beta, bg)
    assert best is not None
    chi2, s0, rc, beta, bg = best
    return {"s0": s0, "rc_arcsec": rc, "beta": beta, "s_bg": bg}, "grid_linear_fallback", chi2, max(int(r.size - 4), 0)


def integrate_beta_flux(s0: float, rc_arcsec: float, beta: float, r1: float, r2: float, ngrid: int = 4096) -> float:
    rr = np.linspace(r1, r2, ngrid)
    yy = beta_component(rr, s0, rc_arcsec, beta) * 2.0 * np.pi * rr
    return float(np.trapezoid(yy, rr))


def make_profile_plot(result: BetaProfileResult, out_png: Path) -> str:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = np.asarray(result.radii_arcsec)
    y = np.asarray(result.sb)
    e = np.asarray(result.sb_err)
    rr = np.linspace(0, result.max_radius_r500 * result.r500_arcsec, 512)
    model = beta_model(rr, result.s0, result.rc_arcsec, result.beta, result.s_bg)
    bg = np.full_like(rr, result.s_bg)

    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    ax.errorbar(r / result.r500_arcsec, y, yerr=e, fmt="o", ms=4, label="profile")
    ax.plot(rr / result.r500_arcsec, model, lw=2, label="beta + constant background")
    ax.plot(rr / result.r500_arcsec, bg, lw=1.4, ls="--", label="constant background")
    ax.axvspan(result.source_inner_r500, result.source_outer_r500, color="cyan", alpha=0.12, label="source")
    ax.axvspan(result.annulus_inner_r500, result.annulus_outer_r500, color="lime", alpha=0.10, label="annulus")
    ax.set_yscale("log")
    ax.set_xlabel("Radius / R500")
    ax.set_ylabel("Surface brightness")
    ax.set_title(f"Beta-model profile, R_EM={result.r_em_annulus_to_source:.3f}")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return str(out_png)


def run_beta_profile(
    image: Path,
    ra: float,
    dec: float,
    r500_arcsec: float,
    out_json: Path,
    out_plot: Path | None = None,
    nbins: int = 20,
    max_radius_r500: float = 2.0,
    source_inner_r500: float = 0.0,
    source_outer_r500: float = 1.0,
    annulus_inner_r500: float = 1.2,
    annulus_outer_r500: float = 1.8,
) -> BetaProfileResult:
    prof = extract_radial_profile(image, ra, dec, r500_arcsec, nbins=nbins, max_radius_r500=max_radius_r500)
    params, method, chi2, dof = fit_beta_profile(prof["radii_arcsec"], prof["sb"], prof["sb_err"], r500_arcsec)
    src_flux = integrate_beta_flux(params["s0"], params["rc_arcsec"], params["beta"], source_inner_r500 * r500_arcsec, source_outer_r500 * r500_arcsec)
    ann_flux = integrate_beta_flux(params["s0"], params["rc_arcsec"], params["beta"], annulus_inner_r500 * r500_arcsec, annulus_outer_r500 * r500_arcsec)
    r_em = ann_flux / src_flux if src_flux > 0 else float("nan")

    result = BetaProfileResult(
        image=str(image),
        center_ra_deg=ra,
        center_dec_deg=dec,
        r500_arcsec=r500_arcsec,
        nbins=nbins,
        max_radius_r500=max_radius_r500,
        radii_arcsec=[float(x) for x in prof["radii_arcsec"]],
        sb=[None if not np.isfinite(x) else float(x) for x in prof["sb"]],  # type: ignore[list-item]
        sb_err=[None if not np.isfinite(x) else float(x) for x in prof["sb_err"]],  # type: ignore[list-item]
        area_arcsec2=[float(x) for x in prof["area_arcsec2"]],
        s0=params["s0"],
        rc_arcsec=params["rc_arcsec"],
        beta=params["beta"],
        s_bg=params["s_bg"],
        fit_method=method,
        chi2=chi2,
        dof=dof,
        r_em_annulus_to_source=float(r_em),
        annulus_inner_r500=annulus_inner_r500,
        annulus_outer_r500=annulus_outer_r500,
        source_inner_r500=source_inner_r500,
        source_outer_r500=source_outer_r500,
        plot_png=None,
    )
    if out_plot is not None:
        result.plot_png = make_profile_plot(result, out_plot)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--ra", type=float, required=True)
    p.add_argument("--dec", type=float, required=True)
    p.add_argument("--r500-arcsec", type=float, required=True)
    p.add_argument("--out-json", type=Path, required=True)
    p.add_argument("--out-plot", type=Path)
    args = p.parse_args()
    result = run_beta_profile(args.image, args.ra, args.dec, args.r500_arcsec, args.out_json, args.out_plot)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
