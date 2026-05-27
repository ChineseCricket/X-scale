#!/usr/bin/env python3
"""Install CALDB ACIS background files from extracted tarball."""
import shutil
import os
import glob

SRC = "/tmp/data/chandra/acis/bkgrnd"
DST = "/data/jyz/Applications/ciao-4.18/ciao-4.18/CALDB/data/chandra/acis/bkgrnd"

files = sorted(glob.glob(os.path.join(SRC, "*.fits")))
print(f"Found {len(files)} FITS files to install")

existing = set(os.listdir(DST))
copied = 0
skipped = 0
for f in files:
    basename = os.path.basename(f)
    if basename in existing:
        skipped += 1
        continue
    shutil.copy2(f, DST)
    copied += 1
    if copied % 20 == 0:
        print(f"  {copied} copied...")

total = len(glob.glob(os.path.join(DST, "*.fits")))
print(f"Done: {copied} copied, {skipped} already existed")
print(f"Total FITS files in CALDB bkgrnd: {total}")
