import os
import glob
import argparse
import subprocess
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Configuration
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = str(PROJECT_DIR / "chandra_data_evt")
DROPPED_LIST = str(PROJECT_DIR / "configs" / "dropped.list")
ENERGY = "500:2000"  # 0.5–2.0 keV
BINSIZE = 1
SIGMIN = 2
SIGMAX = 5

# Locate CIAO init script
CIAO_PATHS = [
    "/data/jyz/Applications/ciao-4.18/ciao-4.18/bin/ciao.sh",
    "/Applications/ciao-4.18/bin/ciao.sh",
]
CIAO_INIT = ""
for p in CIAO_PATHS:
    if os.path.exists(p):
        CIAO_INIT = f"source {p} && "
        break

def load_dropped():
    dropped_clusters = set()
    if os.path.exists(DROPPED_LIST):
        with open(DROPPED_LIST, 'r') as f:
            for line in f:
                c = line.strip()
                if c: dropped_clusters.add(c)
    return dropped_clusters

def run_cmd(cmd, tmpdir=None):
    full_cmd = f"{CIAO_INIT}{cmd}"
    env = os.environ.copy()
    if tmpdir:
        os.makedirs(tmpdir, exist_ok=True)
        env["TMPDIR"] = tmpdir
    subprocess.run(full_cmd, shell=True, check=True, executable='/bin/bash', env=env)

def check_resources(min_cpu_free=4, min_mem_gb=8):
    if not HAS_PSUTIL:
        return True, 0, 0
    cpu_count = psutil.cpu_count()
    cpu_load = os.getloadavg()[0]
    cpu_free = cpu_count - cpu_load
    mem = psutil.virtual_memory()
    mem_free_gb = mem.available / (1024**3)
    ok = cpu_free >= min_cpu_free and mem_free_gb >= min_mem_gb
    return ok, cpu_free, mem_free_gb

def process_cluster(cluster):
    print(f"\n{'='*50}\nProcessing cluster: {cluster}\n{'='*50}")
    cluster_dir = os.path.join(DATA_DIR, cluster)
    raw_dir = os.path.join(cluster_dir, 'raw')
    
    if not os.path.isdir(raw_dir):
        print("  No 'raw' directory found. Skipping.")
        return

    obsdir_names = [d for d in os.listdir(raw_dir) if os.path.isdir(os.path.join(raw_dir, d))]
    
    if not obsdir_names:
        print("  No ObsIDs found. Skipping.")
        return

    outdir = os.path.join(cluster_dir, "processed")
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    cluster_tmpdir = os.path.join(outdir, "tmp")

    # Step 1: chandra_repro each ObsID & filter energy
    evt_list = []
    print("=== Step 1: Reprocessing each ObsID ===")
    for obsid in obsdir_names:
        obs_path = os.path.join(raw_dir, obsid)
        repro_dir = os.path.join(obs_path, "repro")
        
        # 1.1 Reprocess
        # Note: raw directory should contain primary & secondary subdirectories for this to work natively
        has_repro = False
        if not glob.glob(os.path.join(repro_dir, "*acisf*repro*evt2.fits*")):
            # Verify if level 1 event files are present to allow chandra_repro
            if glob.glob(os.path.join(obs_path, "*", "*evt1.fits*")):
                try:
                    run_cmd(f"punlearn chandra_repro; chandra_repro indir='{obs_path}' outdir='{repro_dir}' clobber=yes mode=h")
                    has_repro = True
                except:
                    print(f"    [WARNING] chandra_repro failed for {obsid}.")
            else:
                print(f"    [WARNING] No evt1 files found for {obsid}, skipping chandra_repro.")
        
        # 1.2 Find evt2 (either repro or primary)
        evt2_files = glob.glob(os.path.join(repro_dir, "*acisf*repro*evt2.fits*")) or glob.glob(os.path.join(obs_path, "primary", "*evt2.fits*"))
        if not evt2_files:
            print(f"Error: No event file found for {obsid}!")
            continue
            
        base_evt = evt2_files[0]
        
        # 1.3 Energy filtering
        if not os.path.exists(repro_dir):
            os.makedirs(repro_dir)
            
        evt_band = os.path.join(repro_dir, "evt_band.fits")
        run_cmd(f"punlearn dmcopy; dmcopy '{base_evt}[energy={ENERGY}]' {evt_band} clobber=yes mode=h")
        evt_list.append(evt_band)

    if not evt_list:
        print("  No valid event files processed. Skipping rest of pipeline.")
        return

    # Step 2: Merging observations
    print("=== Step 2: Merging observations ===")
    list_file = os.path.join(outdir, "evt_list.lis")
    with open(list_file, 'w') as f:
        for evt in evt_list:
            f.write(f"{evt}\n")
            
    run_cmd(f"punlearn merge_obs; merge_obs '@{list_file}' '{outdir}/' bin={BINSIZE} clobber=yes mode=h", tmpdir=cluster_tmpdir)
    
    merged_evt = os.path.join(outdir, "merged_evt.fits")
    merged_img = os.path.join(outdir, "merged_flux.img") # Typical output from standard bands but sometimes thresh
    
    # We will compute point sources on the broadband broad_flux.img or merged_evt
    # Use merged_evt binned image to detect sources:
    merged_counts = os.path.join(outdir, "merged_counts.img")
    if not os.path.exists(merged_counts):
        run_cmd(f"punlearn dmcopy; dmcopy '{merged_evt}[bin x=::1,y=::1]' {merged_counts} clobber=yes mode=h")

    # Step 3: Detecting point sources
    print("=== Step 3: Detecting point sources ===")
    src_fits = os.path.join(outdir, "src.fits")
    scell_fits = os.path.join(outdir, "scell.fits")
    imgfile_fits = os.path.join(outdir, "imgfile.fits")
    nbkg_fits = os.path.join(outdir, "nbkg.fits")
    src_reg = os.path.join(outdir, "src.reg")

    run_cmd(f"punlearn wavdetect; wavdetect infile={merged_counts} outfile={src_fits} scellfile={scell_fits} imagefile={imgfile_fits} defnbkgfile={nbkg_fits} scales='2.0 4.0' clobber=yes mode=h", tmpdir=cluster_tmpdir)

    # Step 4: Removing point sources
    print("=== Step 4: Removing point sources ===")
    clean_evt = os.path.join(outdir, "merged_clean_evt.fits")
    run_cmd(f"punlearn dmcopy; dmcopy '{merged_evt}[exclude sky=region({src_fits})]' {clean_evt} clobber=yes mode=h")

    # Step 5: Recomputing flux image
    print("=== Step 5: Recomputing flux image ===")
    clean_fluxed_dir = os.path.join(outdir, "clean_fluxed")
    if not os.path.exists(clean_fluxed_dir):
        os.makedirs(clean_fluxed_dir)
        
    outroot = os.path.join(clean_fluxed_dir, "flux")
    
    # We already have a broad_flux.img from merge_obs. Let's just exclude the regions from it
    broad_flux_img = os.path.join(outdir, "broad_flux.img")
    clean_flux_img = os.path.join(clean_fluxed_dir, "flux_clean.img")
    run_cmd(f"punlearn dmcopy; dmcopy '{broad_flux_img}[exclude sky=region({src_fits})]' {clean_flux_img} clobber=yes mode=h")

    # Step 6: Smoothing
    print("=== Step 6: Smoothing ===")
    flux_img = clean_flux_img
    
    flux_csmooth = os.path.join(clean_fluxed_dir, "flux_csmooth.img")
    
    if os.path.exists(flux_img):
        # Mode=h to avoid prompt block
        run_cmd(f"punlearn csmooth; csmooth infile={flux_img} outfile={flux_csmooth} sigmin={SIGMIN} sigmax={SIGMAX} clobber=yes mode=h", tmpdir=cluster_tmpdir)
        print(f"=== DONE {cluster} ===")
        print(f"Final product: {flux_csmooth}")
    else:
        print(f"=== ERROR {cluster}: Flux image not generated correctly ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIAO pipeline for galaxy cluster X-ray data reduction")
    parser.add_argument("clusters", nargs="*", help="Cluster names to process (default: all non-dropped)")
    parser.add_argument("--no-check", action="store_true", help="Skip resource check")
    args = parser.parse_args()

    dropped = load_dropped()
    all_clusters = sorted(d for d in os.listdir(DATA_DIR)
                          if os.path.isdir(os.path.join(DATA_DIR, d)) and d not in dropped)
    clusters = args.clusters if args.clusters else all_clusters

    if not args.no_check:
        ok, cpu_free, mem_free_gb = check_resources()
        print(f"Resource check: CPU {cpu_free:.1f} cores free, MEM {mem_free_gb:.1f} GB free")
        if not ok:
            print(f"[WARNING] Low resources! Recommended: 4+ CPU cores, 8+ GB RAM")
            resp = input("Continue anyway? [y/N] ").strip().lower()
            if resp != 'y':
                print("Aborted.")
                exit(1)

    for cluster in clusters:
        if cluster in dropped:
            print(f"Skipping dropped cluster: {cluster}")
            continue
        try:
            process_cluster(cluster)
        except subprocess.CalledProcessError as e:
            print(f"  [PIPELINE ABORTED] CIAO returned error: {e}")
        except Exception as e:
            print(f"  [ERROR] {e}")
