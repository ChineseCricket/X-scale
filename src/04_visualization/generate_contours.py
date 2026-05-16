import os
import glob
import subprocess
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Configuration
DATA_DIR = 'chandra_data_evt'
OUTPUT_DIR = 'output_heatmaps'
DROPPED_LIST = 'Dropped.list'

# Parameters for csmooth
# smin, smax parameters control the minimum and maximum significance ratio
SMIN = 3
SMAX = 5

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Load the list of clusters to drop
dropped_clusters = set()
if os.path.exists(DROPPED_LIST):
    with open(DROPPED_LIST, 'r') as f:
        for line in f:
            c = line.strip()
            if c:
                dropped_clusters.add(c)

clusters = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
clusters.sort()

for cluster in clusters:
    # 1. Skip dropped clusters
    if cluster in dropped_clusters:
        print(f"Skipping {cluster} (found in Dropped.list).")
        continue

    print(f"\nProcessing cluster: {cluster}")
    cluster_dir = os.path.join(DATA_DIR, cluster)
    raw_dir = os.path.join(cluster_dir, 'raw')
    
    if not os.path.isdir(raw_dir):
        print(f"  No 'raw' directory found. Skipping.")
        continue
        
    pattern = os.path.join(raw_dir, '*', 'primary', '*evt2.fits*')
    evt_files = glob.glob(pattern)
    
    if len(evt_files) == 0:
        print(f"  No evt2 files found. Skipping.")
        continue
        
    print(f"  Found {len(evt_files)} event files.")
    
    # We will output intermediate CIAO products into a dedicated directory
    ciao_out_dir = os.path.join(cluster_dir, 'ciao_products')
    if not os.path.exists(ciao_out_dir):
        os.makedirs(ciao_out_dir)
        
    merged_img_path = os.path.join(ciao_out_dir, f"{cluster}_merged.fits")
    
    if not os.path.exists(merged_img_path):
        # Use pure Python to map events, since merge_obs fails missing ASOL (aspect solution) files
        all_ra, all_dec = [], []
        wcs_ref = None
        
        for f in evt_files:
            try:
                with fits.open(f) as hdul:
                    data = hdul[1].data
                    header = hdul[1].header
                    x, y = data['x'], data['y']
                    
                    x_col, y_col = 11, 12
                    for i in range(1, 100):
                        if f'TCTYP{i}' in header and header[f'TCTYP{i}'] in ('RA---TAN', 'RA---SIN'): x_col = i
                        if f'TCTYP{i}' in header and header[f'TCTYP{i}'] in ('DEC--TAN', 'DEC--SIN'): y_col = i
                    
                    w = WCS(naxis=2)
                    w.wcs.crpix = [header[f'TCRPX{x_col}'], header[f'TCRPX{y_col}']]
                    w.wcs.cdelt = [header[f'TCDLT{x_col}'], header[f'TCDLT{y_col}']]
                    w.wcs.crval = [header[f'TCRVL{x_col}'], header[f'TCRVL{y_col}']]
                    w.wcs.ctype = [header[f'TCTYP{x_col}'], header[f'TCTYP{y_col}']]
                    
                    if wcs_ref is None:
                        wcs_ref = w
                        
                    sky_coords = w.pixel_to_world(x, y)
                    all_ra.append(sky_coords.ra.deg)
                    all_dec.append(sky_coords.dec.deg)
            except Exception as e:
                print(f"  [ERROR] Error extracting events from {f}: {e}")

        if not all_ra:
            print(f"  [WARNING] No valid events found to merge. Skipping.")
            continue
            
        all_ra = np.concatenate(all_ra)
        all_dec = np.concatenate(all_dec)
        
        # Bin to Image
        pixel_scale_deg = 0.492 / 3600.0
        grid_res = pixel_scale_deg * 4
        ra_bins = np.arange(np.min(all_ra), np.max(all_ra), grid_res)
        dec_bins = np.arange(np.min(all_dec), np.max(all_dec), grid_res)
        H, ra_edges, dec_edges = np.histogram2d(all_ra, all_dec, bins=[ra_bins, dec_bins])
        H = H.T  # Transpose to (Dec, RA)
        
        # Update WCS for the binned image
        wcs_img = WCS(naxis=2)
        wcs_img.wcs.crpix = [1, 1]
        wcs_img.wcs.crval = [ra_edges[0], dec_edges[0]]
        wcs_img.wcs.cdelt = [grid_res, grid_res]
        wcs_img.wcs.ctype = ['RA---TAN', 'DEC--TAN']
        
        # Ensure array is float32 for CIAO
        hdu = fits.PrimaryHDU(H.astype(np.float32), header=wcs_img.to_header())
        hdu.writeto(merged_img_path, overwrite=True)
        print(f"  --> Saved merged counts image to: {merged_img_path}")
    else:
        print(f"  --> Merged image already exists: {merged_img_path}")

    # 4. Call CIAO csmooth to perform adaptive smoothing
    smoothed_img_path = os.path.join(ciao_out_dir, f"{cluster}_smoothed.img")
    smoothed_sig_path = os.path.join(ciao_out_dir, f"{cluster}_sig.fits")
    smoothed_scale_path = os.path.join(ciao_out_dir, f"{cluster}_scales.fits")

    if not os.path.exists(smoothed_img_path):
        print(f"  --> Running csmooth (smin={SMIN}, smax={SMAX})...")
        ciao_init = "source /Applications/ciao-4.18/bin/ciao.sh && " if os.path.exists("/Applications/ciao-4.18/bin/ciao.sh") else ""

        cmd_csmooth = (
            f'{ciao_init}punlearn csmooth; '
            f'csmooth infile="{merged_img_path}" outfile="{smoothed_img_path}" '
            f'outsigfile="{smoothed_sig_path}" outsclfile="{smoothed_scale_path}" '
            f'sclmap="none" sigmin={SMIN} sigmax={SMAX} clobber=yes mode=h'
        )
        try:
            subprocess.run(cmd_csmooth, shell=True, check=True, executable='/bin/bash')
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] csmooth failed: {e}")
            continue
    else:
        print(f"  --> Smoothed image already exists: {smoothed_img_path}")

    # 5. Plotting: Research-grade Heatmaps
    if not os.path.exists(smoothed_img_path):
        print(f"  [ERROR] Smoothed image not found. Skipping plot.")
        continue
        
    print(f"  --> Generating publication-quality heatmap...")
    try:
        with fits.open(smoothed_img_path) as hdul:
            img_data = hdul[0].data
            header = hdul[0].header
            w = WCS(header)
            
            # Clean data array (deal with NaN and zero values for log scale)
            img_data = np.nan_to_num(img_data, nan=0.0)
            
            # Set LogNorm limits
            valid_pixels = img_data[img_data > 0]
            if len(valid_pixels) == 0:
                print(f"  [WARNING] Image only contains zeros/NaNs for {cluster}.")
                continue
                
            vmin = np.percentile(valid_pixels, 1)  # Filter out bottom 1% noise floor
            vmax = np.percentile(valid_pixels, 99.9) # Prevent core over-saturation
            
            # Create Figure
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection=w)
            
            norm = mcolors.LogNorm(vmin=max(vmin, 1e-4), vmax=vmax)
            im = ax.imshow(img_data, origin='lower', cmap='magma', norm=norm)
            
            # Coordinates and Styling
            ax.set_xlabel('RA (J2000)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Dec (J2000)', fontsize=14, fontweight='bold')
            ax.set_title(f'{cluster} X-ray Structure (csmooth {SMIN}-{SMAX})', fontsize=16, fontweight='bold')
            
            # Journal standard inward ticks
            ax.tick_params(axis='both', which='both', direction='in', 
                           color='white', width=1.5, length=6, labelsize=12)
            
            # Minimalistic transparent grid
            ax.grid(color='white', alpha=0.15, linestyle=':', linewidth=1)
            
            # Colorbar
            cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label('Smoothed Counts (log scale)', fontsize=14, fontweight='bold')
            cbar.ax.tick_params(labelsize=12)
            
            output_path = os.path.join(OUTPUT_DIR, f"{cluster}_heatmap.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight', transparent=False, facecolor='black')
            # Black background is optional but often fits magma nicely.
            # To standard publication style, usually white background is safer outside the wcs box:
            fig.patch.set_facecolor('white')
            # So just use standard white facecolor:
            plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"  --> Saved heatmap to {output_path}")
            
    except Exception as e:
        print(f"  [ERROR] Plotting failed for {cluster}: {e}")

print("\nDone processing all clusters.")