#!/usr/bin/env python3
"""Two-step spectral fitting with blank-sky background + XRB modeling.

Step 1: Fit chip-edge background region with XRB model (LHB + halo + CXB)
Step 2: Fit source region (R500) with ICM + frozen XRB model

Usage:
    source /data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh
    python fit_spectral_twostep.py --cluster Abell_0209 --run-all
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from postproces_cluster import (
    CLUSTER_TABLE_PATH,
    ClusterConfig,
    angular_diameter_distance_mpc,
    angular_radius_arcsec,
    apply_region_exclusions,
    compute_r500_mpc,
    default_cluster_dir,
    discover_individual_evt2,
    load_cluster_configs_from_table,
    load_point_source_masks,
    luminosity_distance_cm,
    obsid_from_evt_path,
    resolve_cluster_config,
    run,
    sky_xy_from_event_wcs,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CIAO_SOURCE = "/data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh"
DEFAULT_ENERGY_MIN = 0.5
DEFAULT_ENERGY_MAX = 7.0
DEFAULT_BKG_INNER_R500 = 1.0
DEFAULT_BKG_OUTER_R500 = 3.0
DEFAULT_SHERPA_DIR = "postprocess_r500_blanksky"
DEFAULT_CENTER_MODE = "xray_peak"


# ---------------------------------------------------------------------------
# Blank-sky generation
# ---------------------------------------------------------------------------
def generate_blanksky(evt_path: Path, output_path: Path) -> Path | None:
    """Generate blank-sky background event file for one ObsID."""
    if output_path.exists():
        print(f"[info] Blank-sky exists, skipping: {output_path.name}")
        return output_path
    print(f"[info] Generating blank-sky for {evt_path.name} ...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        run(
            ["blanksky", f"evtfile={evt_path}", f"outfile={output_path}", "clobber=yes"],
            cwd=output_path.parent,
        )
    except Exception as exc:
        print(f"[warn] blanksky failed for {evt_path.name}: {exc}")
        return None
    if not output_path.exists():
        print(f"[warn] blanksky produced no output for {evt_path.name}")
        return None
    return output_path


# ---------------------------------------------------------------------------
# Spectrum extraction
# ---------------------------------------------------------------------------
def extract_one_spectrum(
    cluster_dir: Path,
    evt: Path,
    blanksky: Path,
    region: str,
    outroot: Path,
) -> Path | None:
    """Run specextract for one region, using blank-sky as background."""
    pi_path = Path(str(outroot) + ".pi")
    if pi_path.exists():
        print(f"[info] Spectrum exists, skipping: {pi_path.name}")
        return pi_path
    cmd = [
        "specextract",
        f"infile={evt}[sky={region}]",
        f"bkgfile={blanksky}[sky={region}]",
        f"outroot={outroot}",
        "correctpsf=no",
        "weight=no",
        "bkgresp=no",
        "clobber=yes",
    ]
    try:
        run(cmd, cwd=cluster_dir)
    except Exception as exc:
        print(f"[warn] specextract failed for {outroot.name}: {exc}")
        return None
    return pi_path if pi_path.exists() else None


def extract_all_spectra(
    cluster_dir: Path,
    evt_paths: list[Path],
    outdir: Path,
    name: str,
    center_ra: float,
    center_dec: float,
    r500_arcsec: float,
    bkg_inner_r500: float,
    bkg_outer_r500: float,
    point_source_masks: list,
) -> dict:
    """Extract source + background spectra for all ObsIDs."""
    src_pis = []
    bkg_pis = []
    blanksky_dir = outdir / "blanksky_files"
    blanksky_dir.mkdir(exist_ok=True)

    for evt in evt_paths:
        obsid = obsid_from_evt_path(evt)
        cx, cy, pix_arcsec = sky_xy_from_event_wcs(evt, center_ra, center_dec)
        r500_pix = r500_arcsec / pix_arcsec

        # Generate blank-sky
        bsky_path = blanksky_dir / f"blanksky_obs{obsid}.fits"
        bsky_result = generate_blanksky(evt, bsky_path)
        if bsky_result is None:
            print(f"[warn] Skipping ObsID {obsid} (blank-sky unavailable)")
            continue

        # Point-source exclusion circles in this event file's coordinates
        excl = []
        for m in point_source_masks:
            mx, my, mpa = sky_xy_from_event_wcs(evt, m.ra, m.dec)
            excl.append((mx, my, m.radius_arcsec / mpa))

        # Source region: R500 circle
        src_region = f"circle({cx:.6f},{cy:.6f},{r500_pix:.6f})"
        src_region = apply_region_exclusions(src_region, excl)

        # Background region: annulus beyond R500 (chip clips naturally)
        bkg_in_pix = bkg_inner_r500 * r500_pix
        bkg_out_pix = bkg_outer_r500 * r500_pix
        bkg_region = f"annulus({cx:.6f},{cy:.6f},{bkg_in_pix:.6f},{bkg_out_pix:.6f})"
        bkg_region = apply_region_exclusions(bkg_region, excl)

        tag = "twostep"
        src_outroot = outdir / f"{name}_obs{obsid}_{tag}_src"
        bkg_outroot = outdir / f"{name}_obs{obsid}_{tag}_bkg"

        src_pi = extract_one_spectrum(cluster_dir, evt, bsky_path, src_region, src_outroot)
        bkg_pi = extract_one_spectrum(cluster_dir, evt, bsky_path, bkg_region, bkg_outroot)

        if src_pi:
            src_pis.append(src_pi)
        if bkg_pi:
            bkg_pis.append(bkg_pi)

    return {"src_pis": src_pis, "bkg_pis": bkg_pis}


# ---------------------------------------------------------------------------
# Sherpa script generation
# ---------------------------------------------------------------------------
def write_step1_xrb_script(
    path: Path,
    bkg_pis: list[Path],
    nh_1e22: float,
    out_json: Path,
    out_plot: Path,
    energy_min: float = 0.5,
    energy_max: float = 7.0,
) -> None:
    """Write Sherpa script for Step 1: XRB model fit on background region."""
    spectra_literal = "[" + ", ".join(repr(str(p)) for p in bkg_pis) + "]"
    path.write_text(
        f'''#!/usr/bin/env sherpa
"""Step 1: Fit background region with XRB model (LHB + halo + CXB)."""
from sherpa.astro.ui import *
import json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

set_stat("wstat")
set_method("levmar")

spectra = {spectra_literal}
if not spectra:
    raise SystemExit("No background spectra for XRB fit.")

# XRB model components
gal = xsphabs.gal
lhb = xsapec.lhb
halo = xsapec.halo
cxb = xspowerlaw.cxb

# Galactic absorption
gal.nH = {nh_1e22:.6g}
gal.nH.freeze()

# LHB: unabsorbed thermal, kT well-constrained ~ 0.1 keV
lhb.kT = 0.1
lhb.kT.freeze()
lhb.Abundanc = 1.0
lhb.Abundanc.freeze()
lhb.redshift = 0.0
lhb.redshift.freeze()
lhb.norm = 1e-6

# Galactic halo: absorbed thermal
halo.kT = 0.25
halo.Abundanc = 1.0
halo.Abundanc.freeze()
halo.redshift = 0.0
halo.redshift.freeze()
halo.norm = 1e-6

# CXB: absorbed powerlaw (Γ fixed to literature value)
cxb.PhoIndex = 1.4
cxb.PhoIndex.freeze()
cxb.norm = 1e-5

for i, pha in enumerate(spectra, start=1):
    load_pha(i, pha)
    try:
        ignore_bad()
    except Exception:
        pass
    notice_id(i, {energy_min}, {energy_max})
    group_counts(1, i)
    set_source(i, lhb + gal * (halo + cxb))

fit()
try:
    conf()
    cr = get_conf_results()
except Exception as exc:
    print("[warn] conf() failed:", exc)
    cr = None

# Plot
fig, ax = plt.subplots(figsize=(8, 5))
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, pha in enumerate(spectra, start=1):
    dp = get_data_plot(i)
    mp = get_model_plot(i)
    c = colors[(i - 1) % len(colors)]
    ax.errorbar(dp.x, dp.y, yerr=getattr(dp, "yerr", None), fmt="o", ms=3, color=c, alpha=0.7)
    ax.plot(mp.x, mp.y, color=c, lw=1.5)
ax.set_yscale("log")
ax.set_xlabel("Energy (keV)")
ax.set_ylabel("Counts/s/keV")
ax.set_title("Step 1: XRB model fit (background region)")
ax.grid(alpha=0.2)
fig.savefig("{out_plot}", dpi=150, bbox_inches="tight")
plt.close(fig)

fr = get_fit_results()
xrb_params = {{
    "lhb_kT": float(lhb.kT.val),
    "lhb_norm": float(lhb.norm.val),
    "halo_kT": float(halo.kT.val),
    "halo_norm": float(halo.norm.val),
    "cxb_PhoIndex": float(cxb.PhoIndex.val),
    "cxb_norm": float(cxb.norm.val),
    "gal_nH": float(gal.nH.val),
    "statval": float(fr.statval),
    "dof": int(fr.dof),
    "rstat": float(fr.rstat) if hasattr(fr, "rstat") and fr.rstat is not None else None,
}}
if cr is not None:
    for pn, pv, pm, pp in zip(cr.parnames, cr.parvals, cr.parmins, cr.parmaxes):
        xrb_params["conf_" + str(pn)] = {{"val": float(pv), "lo": float(pm), "hi": float(pp)}}

with open("{out_json}", "w") as f:
    json.dump(xrb_params, f, indent=2)
print(json.dumps(xrb_params, indent=2))
'''
    )


def write_step2_icm_script(
    path: Path,
    src_pis: list[Path],
    xrb_json_path: Path,
    z: float,
    nh_1e22: float,
    out_json: Path,
    out_plot: Path,
    energy_min: float = 0.5,
    energy_max: float = 7.0,
    kt_init: float = 7.0,
) -> None:
    """Write Sherpa script for Step 2: ICM + frozen XRB fit on source region."""
    spectra_literal = "[" + ", ".join(repr(str(p)) for p in src_pis) + "]"
    path.write_text(
        f'''#!/usr/bin/env sherpa
"""Step 2: Fit source region with ICM + frozen XRB model."""
from sherpa.astro.ui import *
import json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

set_stat("wstat")
set_method("levmar")

spectra = {spectra_literal}
if not spectra:
    raise SystemExit("No source spectra for ICM fit.")

# Load XRB parameters from Step 1
with open("{xrb_json_path}") as f:
    xrb = json.load(f)

# Model components (same as Step 1)
gal = xsphabs.gal
lhb = xsapec.lhb
halo = xsapec.halo
cxb = xspowerlaw.cxb
icm = xsapec.icm

gal.nH = {nh_1e22:.6g}
gal.nH.freeze()

# Freeze XRB parameters from Step 1
lhb.kT = xrb["lhb_kT"]; lhb.kT.freeze()
lhb.Abundanc = 1.0; lhb.Abundanc.freeze()
lhb.redshift = 0.0; lhb.redshift.freeze()
lhb.norm = xrb["lhb_norm"]; lhb.norm.freeze()

halo.kT = xrb["halo_kT"]; halo.kT.freeze()
halo.Abundanc = 1.0; halo.Abundanc.freeze()
halo.redshift = 0.0; halo.redshift.freeze()
halo.norm = xrb["halo_norm"]; halo.norm.freeze()

cxb.PhoIndex = xrb["cxb_PhoIndex"]; cxb.PhoIndex.freeze()
cxb.norm = xrb["cxb_norm"]; cxb.norm.freeze()

# ICM: free parameters
icm.kT = {kt_init:.4g}
icm.Abundanc = 0.3
icm.redshift = {z:.8g}
icm.redshift.freeze()
icm.norm = 1e-3

for i, pha in enumerate(spectra, start=1):
    load_pha(i, pha)
    try:
        ignore_bad()
    except Exception:
        pass
    notice_id(i, {energy_min}, {energy_max})
    group_counts(1, i)
    set_source(i, lhb + gal * (halo + cxb + icm))

fit()
try:
    conf()
    cr = get_conf_results()
except Exception as exc:
    print("[warn] conf() failed:", exc)
    cr = None

# L_X via calc_energy_flux (bolometric: 0.01-100 keV rest frame)
z_val = {z:.8g}
dl_cm = {luminosity_distance_cm(z, 70.0, 0.3):.6e}
try:
    flux_obs = calc_energy_flux(0.01 / (1 + z_val), min(100.0 / (1 + z_val), 15.0))
    lx_bol = flux_obs * 4.0 * np.pi * dl_cm ** 2
except Exception:
    lx_bol = None

# Plot
fig, (ax, rax) = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True,
    gridspec_kw={{"height_ratios": [3, 1], "hspace": 0.05}})
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, pha in enumerate(spectra, start=1):
    c = colors[(i - 1) % len(colors)]
    dp = get_data_plot(i)
    mp = get_model_plot(i)
    rp = get_resid_plot(i)
    label = pha.rsplit("/", 1)[-1]
    ax.errorbar(dp.x, dp.y, yerr=getattr(dp, "yerr", None), fmt="o", ms=3, color=c, alpha=0.7, label=label)
    ax.plot(mp.x, mp.y, color=c, lw=1.5)
    rax.errorbar(rp.x, rp.y, yerr=getattr(rp, "yerr", None), fmt="o", ms=3, color=c, alpha=0.7)
rax.axhline(0, color="0.25", lw=0.8, ls="--")
ax.set_yscale("log")
ax.set_ylabel("Counts/s/keV")
rax.set_xlabel("Energy (keV)")
rax.set_ylabel("Residual")
ax.set_title("Step 2: ICM + frozen XRB fit (source region)")
ax.legend(fontsize=7)
ax.grid(alpha=0.2)
rax.grid(alpha=0.2)
fig.savefig("{out_plot}", dpi=150, bbox_inches="tight")
plt.close(fig)

fr = get_fit_results()
rstat = float(fr.rstat) if hasattr(fr, "rstat") and fr.rstat is not None else None
qval = float(fr.qval) if hasattr(fr, "qval") and fr.qval is not None else None
conf_dict = {{}}
if cr is not None:
    for pn, pv, pm, pp in zip(cr.parnames, cr.parvals, cr.parmins, cr.parmaxes):
        conf_dict[str(pn)] = {{"val": float(pv), "lo": float(pm), "hi": float(pp)}}

result = {{
    "temperature_keV": float(icm.kT.val),
    "abundance_solar": float(icm.Abundanc.val),
    "apec_norm": float(icm.norm.val),
    "redshift": float(icm.redshift.val),
    "nH_1e22": float(gal.nH.val),
    "lx_bol_erg_s": float(lx_bol) if lx_bol is not None else None,
    "statval": float(fr.statval),
    "dof": int(fr.dof),
    "rstat": rstat,
    "qval": qval,
    "n_spectra": len(spectra),
    "xrb_params_frozen": xrb,
    "confidence": conf_dict,
    "model": "lhb + phabs*(halo + cxb + icm)",
    "fit_plot_png": "{out_plot}",
}}
with open("{out_json}", "w") as f:
    json.dump(result, f, indent=2, sort_keys=True)
print(json.dumps(result, indent=2, sort_keys=True))
'''
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cluster", required=True, help="Cluster key/name")
    p.add_argument("--cluster-table", type=Path, default=CLUSTER_TABLE_PATH)
    p.add_argument("--outdir-name", default=DEFAULT_SHERPA_DIR, help="Output subdirectory name")
    p.add_argument("--z", type=float, default=None, help="Override redshift")
    p.add_argument("--m500", type=float, default=None, help="Override M500")
    p.add_argument("--h0", type=float, default=70.0)
    p.add_argument("--omega-m", type=float, default=0.3)
    p.add_argument("--nh", type=float, default=None, help="Override nH (1e22 cm^-2)")
    p.add_argument("--energy-min", type=float, default=DEFAULT_ENERGY_MIN)
    p.add_argument("--energy-max", type=float, default=DEFAULT_ENERGY_MAX)
    p.add_argument("--bkg-inner-r500", type=float, default=DEFAULT_BKG_INNER_R500)
    p.add_argument("--bkg-outer-r500", type=float, default=DEFAULT_BKG_OUTER_R500)
    p.add_argument("--mask-point-sources", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--generate-blanksky", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--extract-spectra", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--run-sherpa", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--fit-method", default="levmar", help="Sherpa optimizer")
    p.add_argument("--ps-sigma-min", type=float, default=3.0)
    p.add_argument("--ps-radius-scale", type=float, default=1.5)
    p.add_argument("--ps-min-radius-pix", type=float, default=6.0)
    p.add_argument("--ps-skip-center-r500", type=float, default=0.05)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if shutil.which("blanksky") is None:
        raise SystemExit(f"CIAO not on PATH. Run: source {CIAO_SOURCE}")

    configs = load_cluster_configs_from_table(args.cluster_table)
    config_key, config = resolve_cluster_config(args.cluster, configs)
    cluster_dir = default_cluster_dir(config_key, config)
    if cluster_dir is None:
        raise SystemExit(f"No data directory for {config_key}")
    cluster_dir = cluster_dir.resolve()

    redshift = args.z if args.z is not None else config.redshift
    m500_raw = args.m500 if args.m500 is not None else config.m500
    if redshift is None or m500_raw is None:
        raise SystemExit(f"Need redshift and M500 for {config_key}")
    h = args.h0 / 100.0
    m500_msun = m500_raw / h if config.m500_h_inverse else m500_raw
    nh = args.nh if args.nh is not None else config.nh_1e22

    r500_mpc = compute_r500_mpc(m500_msun, redshift, args.h0, args.omega_m)
    r500_arcsec = angular_radius_arcsec(r500_mpc, redshift, args.h0, args.omega_m)

    print(f"[info] Cluster: {config_key}")
    print(f"  z={redshift:.4f}, M500={m500_msun:.2e} Msun, R500={r500_arcsec:.1f}\"")
    print(f"  nH={nh:.4g} x1e22 cm^-2")

    outdir = cluster_dir / args.outdir_name
    outdir.mkdir(exist_ok=True)
    name = config_key

    # Discover event files
    evt_paths = discover_individual_evt2(cluster_dir)
    if not evt_paths:
        raise SystemExit(f"No event files found in {cluster_dir}")
    print(f"[info] Found {len(evt_paths)} ObsIDs: {[obsid_from_evt_path(e) for e in evt_paths]}")

    # Point source masks
    psmask = (
        load_point_source_masks(
            cluster_dir,
            "processed/src.fits",
            config.center_ra,
            config.center_dec,
            r500_arcsec,
            args.bkg_outer_r500,
            args.ps_sigma_min,
            args.ps_radius_scale,
            args.ps_min_radius_pix,
            args.ps_skip_center_r500,
        )
        if args.mask_point_sources
        else []
    )

    # Use catalog center (could add xray_peak mode later)
    center_ra = config.center_ra
    center_dec = config.center_dec

    # --- Extract spectra ---
    if args.extract_spectra:
        spectra = extract_all_spectra(
            cluster_dir,
            evt_paths,
            outdir,
            name,
            center_ra,
            center_dec,
            r500_arcsec,
            args.bkg_inner_r500,
            args.bkg_outer_r500,
            psmask,
        )
    else:
        # Find existing spectra
        spectra = {
            "src_pis": sorted(outdir.glob(f"{name}_obs*_twostep_src.pi")),
            "bkg_pis": sorted(outdir.glob(f"{name}_obs*_twostep_bkg.pi")),
        }

    src_pis = spectra["src_pis"]
    bkg_pis = spectra["bkg_pis"]
    print(f"[info] Source spectra: {len(src_pis)}, Background spectra: {len(bkg_pis)}")

    if not src_pis or not bkg_pis:
        raise SystemExit("Missing spectra. Run with --extract-spectra first.")

    kt_init = 5.0 * (m500_msun / 3e14) ** (2.0 / 3.0)

    # --- Step 1: XRB fit ---
    step1_script = outdir / f"fit_{name}_step1_xrb.py"
    step1_json = outdir / f"{name}_step1_xrb_results.json"
    step1_plot = outdir / f"{name}_step1_xrb_fit_plot.png"

    write_step1_xrb_script(
        step1_script,
        bkg_pis,
        nh,
        step1_json,
        step1_plot,
        args.energy_min,
        args.energy_max,
    )
    print(f"[info] Step 1 XRB script: {step1_script}")

    if args.run_sherpa:
        print("[info] Running Step 1: XRB fit ...")
        run(["sherpa", str(step1_script)], cwd=outdir)

    if not step1_json.exists():
        raise SystemExit(f"Step 1 results not found: {step1_json}")

    # --- Step 2: ICM + frozen XRB fit ---
    step2_script = outdir / f"fit_{name}_step2_icm.py"
    step2_json = outdir / f"{name}_step2_icm_results.json"
    step2_plot = outdir / f"{name}_step2_icm_fit_plot.png"

    write_step2_icm_script(
        step2_script,
        src_pis,
        step1_json,
        redshift,
        nh,
        step2_json,
        step2_plot,
        args.energy_min,
        args.energy_max,
        kt_init,
    )
    print(f"[info] Step 2 ICM script: {step2_script}")

    if args.run_sherpa:
        print("[info] Running Step 2: ICM + frozen XRB fit ...")
        run(["sherpa", str(step2_script)], cwd=outdir)

    if step2_json.exists():
        with open(step2_json) as f:
            result = json.load(f)
        print(f"\n{'='*50}")
        print(f"  T_X = {result['temperature_keV']:.2f} keV")
        print(f"  L_X = {result.get('lx_bol_erg_s', 'N/A')} erg/s")
        print(f"  rstat = {result.get('rstat', 'N/A')}")
        print(f"  n_spectra = {result['n_spectra']}")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
