#!/usr/bin/env python3
"""Spectral fitting with beta-model constrained ICM correction.

Current problem: local annulus (1.2-1.8 R500) background is contaminated by ICM
for low-z clusters. WSTAT oversubtracts this ICM, biasing T_X high.

Solution: add a second apec component to the source model that represents the
oversubtracted ICM from the annulus. The component's norm is constrained by
the beta-model emission measure ratio (R_EM) and the BACKSCAL area ratio.

Model: phabs * (apec_icm + apec_correction)
- apec_correction.kT = apec_icm.kT * f_T (annulus temperature fraction)
- apec_correction.norm = apec_icm.norm * alpha * R_EM / (1 - alpha * R_EM)

Uses EXISTING spectra from postprocess_r500/ (local annulus WSTAT background).
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from postproces_cluster import (
    CLUSTER_TABLE_PATH,
    angular_radius_arcsec,
    compute_r500_mpc,
    default_cluster_dir,
    load_cluster_configs_from_table,
    luminosity_distance_cm,
    resolve_cluster_config,
    run,
)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cluster", required=True)
    p.add_argument("--cluster-table", type=Path, default=CLUSTER_TABLE_PATH)
    p.add_argument("--h0", type=float, default=70.0)
    p.add_argument("--omega-m", type=float, default=0.3)
    p.add_argument("--energy-min", type=float, default=0.5)
    p.add_argument("--energy-max", type=float, default=7.0)
    p.add_argument("--bkg-inner-r500", type=float, default=1.2)
    p.add_argument("--bkg-outer-r500", type=float, default=1.8)
    p.add_argument("--t-ann-frac", type=float, default=0.5, help="T_annulus / T_source ratio")
    p.add_argument("--free-abundance", action="store_true")
    p.add_argument("--run-sherpa", action=argparse.BooleanOptionalAction, default=True)
    return p.parse_args()


def compute_alpha(bkg_inner_r500, bkg_outer_r500):
    """BACKSCAL area ratio: source_area / annulus_area."""
    src_area = 1.0 ** 2  # πR500², R500=1
    ann_area = bkg_outer_r500**2 - bkg_inner_r500**2
    return src_area / ann_area


def write_sherpa_script(path, spectra, z, nh, kt_init, R_EM, alpha, t_frac,
                        out_json, out_plot, energy_min, energy_max, free_abundance):
    """Write Sherpa script with beta-model ICM correction."""
    spectra_lit = "[" + ", ".join(repr(str(p)) for p in spectra) + "]"
    # Correction factor: norm_correction / norm_icm
    factor = alpha * R_EM / (1.0 - alpha * R_EM) if (1.0 - alpha * R_EM) > 0 else 0.0
    abund_thaw = "\nicm.Abundanc.thaw()" if free_abundance else ""

    free_abund_bool = "True" if free_abundance else "False"
    path.write_text(f'''#!/usr/bin/env sherpa
"""ICM fit with beta-model annulus ICM correction."""
from sherpa.astro.ui import *
import json, numpy as np
__FREE_ABUND__ = {free_abund_bool}
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

set_stat("wstat")
set_method("levmar")

spectra = {spectra_lit}
if not spectra:
    raise SystemExit("No spectra.")

gal = xsphabs.gal
icm = xsapec.icm
corr = xsapec.corr

gal.nH = {nh:.6g}
gal.nH.freeze()

icm.kT = {kt_init:.4g}
icm.Abundanc = 0.3{abund_thaw}
icm.redshift = {z:.8g}
icm.redshift.freeze()
icm.norm = 1e-3

# Correction component: ICM oversubtracted from annulus
corr.kT = {t_frac:.4g}  # linked via ratio, multiply after fit
corr.Abundanc = icm.Abundanc  # shared abundance
corr.redshift = icm.redshift
corr.norm = {factor:.6g}  # linked via ratio

for i, pha in enumerate(spectra, start=1):
    load_pha(i, pha)
    try: ignore_bad()
    except: pass
    notice_id(i, {energy_min}, {energy_max})
    group_counts(1, i)
    set_source(i, gal * (icm + corr))

# Link corr parameters to icm parameters
corr.kT = {t_frac:.4g} * icm.kT
corr.norm = {factor:.6g} * icm.norm

fit()
C_free = None
if __FREE_ABUND__:
    # Fixed abundance fit for LRT comparison
    icm.Abundanc = 0.3
    icm.Abundanc.freeze()
    fit()
    C_fixed = get_fit_results().statval
    icm.Abundanc.thaw()
    fit()
    C_free = get_fit_results().statval
    delta_C = C_fixed - C_free
    print(f"[info] LRT: C_fixed={{C_fixed:.1f}}, C_free={{C_free:.1f}}, delta_C={{delta_C:.1f}}")
    if delta_C < 3.84:
        print("[info] Free abundance not significant (p>0.05), using fixed 0.3")
        icm.Abundanc = 0.3
        icm.Abundanc.freeze()
        fit()
    else:
        print("[info] Free abundance significant (p<0.05)")

try:
    conf()
    cr = get_conf_results()
except Exception as exc:
    print(f"[warn] conf failed: {{exc}}")
    cr = None

# L_X
z_val = {z:.8g}
dl_cm = {luminosity_distance_cm(z, 70.0, 0.3):.6e}
try:
    flux = calc_energy_flux(0.01/(1+z_val), min(100.0/(1+z_val), 15.0))
    lx_bol = flux * 4.0 * np.pi * dl_cm**2
except:
    lx_bol = None

# Plot
fig, (ax, rax) = plt.subplots(2, 1, figsize=(8, 6.2), sharex=True,
    gridspec_kw={{"height_ratios": [3, 1], "hspace": 0.05}})
colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, pha in enumerate(spectra, start=1):
    c = colors[(i-1) % len(colors)]
    dp = get_data_plot(i); mp = get_model_plot(i); rp = get_resid_plot(i)
    label = pha.rsplit("/", 1)[-1].replace("_xray_peak_psmask", "")
    ax.errorbar(dp.x, dp.y, yerr=getattr(dp, "yerr", None), fmt="o", ms=3, color=c, alpha=0.7, label=label)
    ax.plot(mp.x, mp.y, color=c, lw=1.5)
    rax.errorbar(rp.x, rp.y, yerr=getattr(rp, "yerr", None), fmt="o", ms=3, color=c, alpha=0.7)
rax.axhline(0, color="0.25", lw=0.8, ls="--")
ax.set_yscale("log"); ax.set_ylabel("Counts/s/keV")
rax.set_xlabel("Energy (keV)"); rax.set_ylabel("Residual")
ax.set_title(f"ICM fit with beta-model correction (R_EM={R_EM:.4f}, alpha={alpha:.3f})")
ax.legend(fontsize=7); ax.grid(alpha=0.2); rax.grid(alpha=0.2)
fig.savefig("{out_plot}", dpi=150, bbox_inches="tight")
plt.close(fig)

fr = get_fit_results()
rstat = float(fr.rstat) if hasattr(fr, "rstat") and fr.rstat is not None else None
qval = float(fr.qval) if hasattr(fr, "qval") and fr.qval is not None else None
conf_dict = {{}}
if cr:
    for pn, pv, pm, pp in zip(cr.parnames, cr.parvals, cr.parmins, cr.parmaxes):
        conf_dict[str(pn)] = {{"val": float(pv), "lo": float(pm), "hi": float(pp)}}

result = {{
    "temperature_keV": float(icm.kT.val),
    "abundance_solar": float(icm.Abundanc.val),
    "apec_norm": float(icm.norm.val),
    "correction_norm": float(corr.norm.val),
    "correction_factor": {factor:.6g},
    "R_EM": {R_EM:.6g},
    "alpha": {alpha:.6g},
    "t_frac": {t_frac:.4g},
    "lx_bol_erg_s": float(lx_bol) if lx_bol is not None else None,
    "statval": float(fr.statval),
    "dof": int(fr.dof),
    "rstat": rstat,
    "qval": qval,
    "n_spectra": len(spectra),
    "free_abundance": __FREE_ABUND__,
    "lrt_deltaC": float(delta_C) if C_free else None,
    "confidence": conf_dict,
    "model": "phabs*(apec_icm + apec_correction)",
}}
with open("{out_json}", "w") as f:
    json.dump(result, f, indent=2, sort_keys=True)
print(json.dumps(result, indent=2, sort_keys=True))
''')


def main():
    args = parse_args()

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
    nh = config.nh_1e22 or 0.02

    r500_mpc = compute_r500_mpc(m500_msun, redshift, args.h0, args.omega_m)
    r500_arcsec = angular_radius_arcsec(r500_mpc, redshift, args.h0, args.omega_m)
    name = config_key
    alpha = compute_alpha(args.bkg_inner_r500, args.bkg_outer_r500)

    print(f"[info] {name}: z={redshift:.4f}, R500={r500_arcsec:.1f}\"")
    print(f"[info] alpha={alpha:.4f} (source_area/annulus_area)")

    # --- Step 0: beta-model ---
    outdir = cluster_dir / "postprocess_r500"
    beta_json = cluster_dir / "postprocess_r500_blanksky" / f"{name}_beta_model.json"

    if beta_json.exists():
        with open(beta_json) as f:
            beta = json.load(f)
        R_EM = beta.get("R_EM_direct", beta.get("R_EM", 0.05))
        R_EM = max(R_EM, 0.001)
    else:
        print("[warn] No beta-model profile; using R_EM=0.05 default")
        R_EM = 0.05

    print(f"[info] R_EM={R_EM:.4f}, correction factor={alpha*R_EM/(1-alpha*R_EM):.4f}")

    # --- Find existing spectra from postprocess_r500/ ---
    # Use existing pipeline spectra (local annulus as WSTAT background)
    spectra = sorted(outdir.glob(f"{name}_obs*_r500_xray_peak_psmask.pi"))
    if not spectra:
        spectra = sorted(outdir.glob(f"{name}_obs*_r500_*_psmask.pi"))
    if not spectra:
        spectra = sorted(outdir.glob(f"{name}_obs*_r500*.pi"))
    print(f"[info] Found {len(spectra)} existing spectra")

    if not spectra:
        raise SystemExit(f"No spectra found in {outdir}")

    kt_init = 5.0 * (m500_msun / 3e14) ** (2.0 / 3.0)
    tag = "correction"

    # --- Sherpa fit ---
    sherpa_script = outdir / f"fit_{name}_{tag}.py"
    fit_json = outdir / f"{name}_{tag}_results.json"
    fit_plot = outdir / f"{name}_{tag}_fit.png"

    write_sherpa_script(
        sherpa_script, spectra, redshift, nh, kt_init,
        R_EM, alpha, args.t_ann_frac,
        fit_json, fit_plot,
        args.energy_min, args.energy_max,
        args.free_abundance,
    )
    print(f"[info] Sherpa script: {sherpa_script}")

    if args.run_sherpa:
        if shutil.which("sherpa") is None:
            print("[warn] sherpa not found")
        else:
            run(["sherpa", str(sherpa_script)], cwd=outdir)

    if fit_json.exists():
        with open(fit_json) as f:
            result = json.load(f)
        print(f"\n{'='*50}")
        print(f"  T_X = {result['temperature_keV']:.2f} keV")
        print(f"  Abundance = {result['abundance_solar']:.2f} solar")
        print(f"  Correction factor = {result['correction_factor']:.6f}")
        print(f"  rstat = {result.get('rstat', 'N/A')}")
        print(f"  L_X = {result.get('lx_bol_erg_s', 'N/A')} erg/s")
        if result.get('lrt_deltaC'):
            print(f"  DeltaC (free vs fixed abundance) = {result['lrt_deltaC']:.1f}")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
