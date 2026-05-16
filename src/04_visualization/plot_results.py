import os
import glob
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Configuration
DATA_DIR = 'chandra_data_evt'
OUTPUT_DIR = 'output_plots'
DROPPED_LIST = 'Dropped.list'

# Contours setup
LEVELS_PERCENTILES = [50, 70, 85, 90, 95, 99.5]

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Load the list of clusters to drop
dropped_clusters = set()
if os.path.exists(DROPPED_LIST):
    with open(DROPPED_LIST, 'r') as f:
        for line in f:
            c = line.strip()
            if c: dropped_clusters.add(c)

clusters = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))])

for cluster in clusters:
    if cluster in dropped_clusters:
        continue

    print(f"\nPlotting cluster: {cluster}")
    
    # We expect the CIAO pipeline to put the smoothed flux image here: 
    # {cluster}/processed/clean_fluxed/flux_csmooth.img
    # Alternatively try the previous fallback location:
    # {cluster}/ciao_products/{cluster}_smoothed.img
    
    cluster_dir = os.path.join(DATA_DIR, cluster)
    flux_img_path = os.path.join(cluster_dir, "processed", "clean_fluxed", "flux_csmooth.img")
    
    # Fallback to pure merged/smoothed file if CIAO full pipeline wasn't finished
    if not os.path.exists(flux_img_path):
        flux_img_path = os.path.join(cluster_dir, "ciao_products", f"{cluster}_smoothed.img")
        
    if not os.path.exists(flux_img_path):
        print(f"  [ERROR] Cannot find smoothed flux image for {cluster}. Run the CIAO pipeline first.")
        continue

    print(f"  --> Loading {flux_img_path}")
    try:
        with fits.open(flux_img_path) as hdul:
            # WCS usually resides in primary HDU if csmooth or fluximage
            img_data = hdul[0].data
            header = hdul[0].header
            
            # WCS parsing handles the sky projection
            w = WCS(header)
            
            # Data cleanup (avoid negatives or NaNs from the background areas)
            img_data = np.nan_to_num(img_data, nan=0.0)
            valid_pixels = img_data[img_data > 0]
            
            if len(valid_pixels) == 0:
                print(f"  [WARNING] Array for {cluster} is empty/all zero.")
                continue

            vmin_lin = np.percentile(valid_pixels, 1)
            vmax_lin = np.percentile(valid_pixels, 99.9)

            # =================================================================
            # Plot 1: Linear Contours
            # =================================================================
            print("  --> Drawing Linear Contours...")
            fig_cont = plt.figure(figsize=(10, 8))
            ax_cont = fig_cont.add_subplot(111, projection=w)
            ax_cont.set_aspect('equal')
            
            # Create linear spaced contours between the 50th and 99.5th percentile of the brightness
            base_lev_min = np.percentile(valid_pixels, 50)
            base_lev_max = np.percentile(valid_pixels, 99.5)
            # Make 8 linear steps
            linear_levels = np.linspace(base_lev_min, base_lev_max, 8)
            
            # Plot contours
            # Using 'viridis' colormap to show scale linearly
            cs = ax_cont.contour(img_data, levels=linear_levels, cmap='viridis', linewidths=1.5, origin='lower')
            
            ax_cont.set_xlabel('RA (J2000)', fontsize=14, fontweight='bold')
            ax_cont.set_ylabel('Dec (J2000)', fontsize=14, fontweight='bold')
            ax_cont.set_title(f'{cluster} X-ray Contours (Linear)', fontsize=16, fontweight='bold')
            ax_cont.coords.grid(color='grey', alpha=0.5, linestyle=':')
            
            # Linear colorbar for contour
            cbar_cont = plt.colorbar(cs, ax=ax_cont, fraction=0.046, pad=0.04)
            cbar_cont.set_label('Smoothed Flux (Linear Scale)', fontsize=14, fontweight='bold')
            
            cont_out = os.path.join(OUTPUT_DIR, f"{cluster}_contours_linear.png")
            fig_cont.savefig(cont_out, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig_cont)
            
            # =================================================================
            # Plot 2: Heatmap
            # =================================================================
            print("  --> Drawing Heatmap...")
            fig_heat = plt.figure(figsize=(10, 8))
            ax_heat = fig_heat.add_subplot(111, projection=w)
            
            # User noted "heatmap is not good to show morphology", but we still provide it as requested
            # We apply LogNorm to the heatmap so the faint structures aren't completely lost compared to the core
            # X-ray flux is very small, e.g. ~1e-10. Do not use max(..., 1e-6) because it severely truncates the map.
            heat_vmin = np.percentile(valid_pixels, 1)
            heat_vmax = np.percentile(valid_pixels, 99.9)
            norm_log = mcolors.LogNorm(vmin=heat_vmin, vmax=heat_vmax)
            
            im = ax_heat.imshow(img_data, origin='lower', cmap='magma', norm=norm_log)
            
            ax_heat.set_xlabel('RA (J2000)', fontsize=14, fontweight='bold')
            ax_heat.set_ylabel('Dec (J2000)', fontsize=14, fontweight='bold')
            ax_heat.set_title(f'{cluster} X-ray Heatmap', fontsize=16, fontweight='bold')
            ax_heat.coords.grid(color='white', alpha=0.2, linestyle=':')
            
            # Log colorbar for heatmap
            cbar_heat = plt.colorbar(im, ax=ax_heat, fraction=0.046, pad=0.04)
            cbar_heat.set_label('Smoothed Flux (Log Scale)', fontsize=14, fontweight='bold')
            
            heat_out = os.path.join(OUTPUT_DIR, f"{cluster}_heatmap_log.png")
            fig_heat.savefig(heat_out, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close(fig_heat)

            print(f"  [SUCCESS] Saved plots to {OUTPUT_DIR}/")
            
    except Exception as e:
        print(f"  [ERROR] Plotting failed for {cluster}: {e}")

print("\nDone rendering all available clusters.")