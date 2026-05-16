#!/bin/bash

# =========================
# 用户参数
# =========================
OBSIDS=("12345" "67890")     # ← 修改为你的 ObsID
ENERGY="500:2000"            # 0.5–2.0 keV
BINSIZE=1
OUTDIR="merged"
SIGMIN=2
SIGMAX=5

# =========================
# 初始化 CIAO
# =========================
ciao

# =========================
# Step 1: 各 ObsID 单独处理
# =========================
echo "=== Step 1: Reprocessing each ObsID ==="

EVT_LIST=()

for OBSID in "${OBSIDS[@]}"; do
    echo "Processing ObsID: $OBSID"

    INDIR="./$OBSID"
    REPODIR="$INDIR/repro"

    # 1.1 标准重处理
    chandra_repro indir=$INDIR outdir=$REPODIR clobber=yes

    # 1.2 找 evt2 文件
    EVT=$(ls $REPODIR/acisf*evt2.fits)

    # 1.3 能段筛选
    EVT_BAND="$REPODIR/evt_band.fits"
    dmcopy "${EVT}[energy=$ENERGY]" $EVT_BAND clobber=yes

    EVT_LIST+=($EVT_BAND)
done

# =========================
# Step 2: 合并 ObsID
# =========================
echo "=== Step 2: Merging observations ==="

# 写入列表文件
rm -f evt_list.lis
for EVT in "${EVT_LIST[@]}"; do
    echo $EVT >> evt_list.lis
done

# 使用 CIAO 合并工具
merge_obs "@evt_list.lis" $OUTDIR/ bin=$BINSIZE clobber=yes

# 输出：
# $OUTDIR/merged_evt.fits
# $OUTDIR/merged_flux.img

# =========================
# Step 3: 自动点源检测
# =========================
echo "=== Step 3: Detecting point sources ==="

MERGED_IMG="$OUTDIR/merged_flux.img"

wavdetect infile=$MERGED_IMG \
          outfile=$OUTDIR/src.fits \
          scellfile=$OUTDIR/scell.fits \
          imagefile=$OUTDIR/imgfile.fits \
          defnbkgfile=$OUTDIR/nbkg.fits \
          clobber=yes

# 生成 region 文件
dmcopy "$OUTDIR/src.fits[cols ra,dec]" $OUTDIR/src.reg clobber=yes

# =========================
# Step 4: 去点源（在 merged evt 上）
# =========================
echo "=== Step 4: Removing point sources ==="

MERGED_EVT="$OUTDIR/merged_evt.fits"
CLEAN_EVT="$OUTDIR/merged_clean_evt.fits"

dmcopy "${MERGED_EVT}[exclude sky=region($OUTDIR/src.reg)]" \
       $CLEAN_EVT clobber=yes

# =========================
# Step 5: 重新做曝光校正（关键）
# =========================
echo "=== Step 5: Recomputing flux image ==="

fluximage $CLEAN_EVT \
          outroot=$OUTDIR/clean_fluxed \
          bands=0.5:2.0:1.0 \
          binsize=$BINSIZE \
          clobber=yes

# 输出：
# clean_fluxed/flux.img ← 最终科学图像

# =========================
# Step 6: 自适应平滑
# =========================
echo "=== Step 6: Smoothing ==="

csmooth infile=$OUTDIR/clean_fluxed/flux.img \
         outfile=$OUTDIR/clean_fluxed/flux_csmooth.img \
         sigmin=$SIGMIN sigmax=$SIGMAX clobber=yes

# =========================
# 完成
# =========================
echo "=== DONE ==="
echo "Final products:"
echo "$OUTDIR/clean_fluxed/flux.img"
echo "$OUTDIR/clean_fluxed/flux_csmooth.img"