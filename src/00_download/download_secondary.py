import os
import glob
import subprocess

# Configuration
# Using a symlink without spaces because CIAO chandra_repro rejects paths with spaces
DATA_DIR = '/tmp/ciao_data'
DROPPED_LIST = 'Dropped.list'

# Types of files strictly requested by chandra_repro
DEFAULT_FILETYPES = "evt1,asol,bpix,msk,mtl,flt,pbk,stat,vv"

# Locate CIAO init script
CIAO_INIT = "source /Applications/ciao-4.18/bin/ciao.sh && " if os.path.exists("/Applications/ciao-4.18/bin/ciao.sh") else ""

def load_dropped():
    dropped_clusters = set()
    if os.path.exists(DROPPED_LIST):
        with open(DROPPED_LIST, 'r') as f:
            for line in f:
                c = line.strip()
                if c: dropped_clusters.add(c)
    return dropped_clusters

def run_cmd(cmd, cwd=None):
    full_cmd = f"{CIAO_INIT}{cmd}"
    subprocess.run(full_cmd, shell=True, check=True, cwd=cwd, executable='/bin/bash')

def download_missing_secondary(cluster):
    cluster_dir = os.path.join(DATA_DIR, cluster)
    raw_dir = os.path.join(cluster_dir, 'raw')
    
    if not os.path.isdir(raw_dir):
        return

    obsdir_names = [d for d in os.listdir(raw_dir) if os.path.isdir(os.path.join(raw_dir, d))]
    
    if not obsdir_names:
        return

    print(f"\n==================================================")
    print(f"Downloading secondary for cluster: {cluster}")
    print(f"==================================================")

    for obsid in obsdir_names:
        obs_path = os.path.join(raw_dir, obsid)
        
        # Check if evt1 or asol already exists
        secondary_dir = os.path.join(obs_path, 'secondary')
        primary_dir = os.path.join(obs_path, 'primary')
        
        missing_files = True
        if not glob.glob(os.path.join(primary_dir, "*asol*")) and not glob.glob(os.path.join(secondary_dir, "*asol*")):
            missing_files = True
        if not glob.glob(os.path.join(primary_dir, "*evt1*")) and not glob.glob(os.path.join(secondary_dir, "*evt1*")):
            missing_files = True
            
        if not missing_files:
            print(f"  [SKIP] ObsID {obsid} already seems to have evt1/asol.")
            continue
            
        print(f"  [DOWNLOAD] Fetching {DEFAULT_FILETYPES} for ObsID {obsid} into {raw_dir}...")
        # download_chandra_obsid saves into the current directory with a folder named as the ObsID
        # e.g., if we run `download_chandra_obsid 3250` in raw_dir, it updates raw_dir/3250/
        cmd = f"download_chandra_obsid {obsid} {DEFAULT_FILETYPES}"
        try:
            run_cmd(cmd, cwd=raw_dir)
            print(f"  [SUCCESS] Downloaded for {obsid}.")
        except subprocess.CalledProcessError as e:
            print(f"  [ERROR] Failed to download {obsid}: {e}")

if __name__ == "__main__":
    dropped = load_dropped()
    
    if not os.path.exists(DATA_DIR):
        print(f"Error: {DATA_DIR} does not exist. Remember to create the symlink:")
        print(f"ln -s \"/Users/jing-yizhang/Documents/Lecture/Advanced Observational Astrophysics/Final Project/chandra_data_evt\" /tmp/ciao_data")
        exit(1)

    clusters = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))])
    
    for cluster in clusters:
        if cluster in dropped:
            print(f"Skipping {cluster} (in Dropped.list).")
            continue
        try:
            download_missing_secondary(cluster)
        except Exception as e:
            print(f"  [ERROR] {e}")

    print("\nAll downloads checked/completed!")
