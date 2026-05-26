#!/usr/bin/env bash
# Batch specextract + spectral fitting for all 23 clusters
set -e

PROJECT="/data/jyz/X_scale"
cd "$PROJECT"

CLUSTERS=(
    Abell_0068  Abell_0209  Abell_0267  Abell_0383  Abell_0586
    Abell_0611  Abell_0697  Abell_0750  Abell_2261
    MACSJ0329.7-0211  MACSJ0429.6-0253  MACSJ0647.7+7015
    MACSJ0744.9+3927  MACSJ1115.9+0129  MACSJ1206.2-0847
    MACSJ1720.3+3536  MACSJ1931.8-2635  MS2137-2353
    RXJ1347.5-1145  RXJ1532.9+3021  RXJ2129.7+0005
    RXJ2248.7-4431  ZwCl_0857.9+2107
)

N=${#CLUSTERS[@]}
echo "Processing $N clusters from $(pwd)..."

for i in $(seq 0 $((N-1))); do
    cluster="${CLUSTERS[$i]}"
    echo ""
    echo "===== [$((i+1))/$N] $cluster ====="

    n_spectra=$(ls chandra_data_evt/${cluster}/postprocess_r500/${cluster}_obs*_r500_*_psmask.pi 2>/dev/null | wc -l)
    if [ "$n_spectra" -eq 0 ]; then
        echo "Running specextract..."
        python src/02_spectral/postproces_cluster.py \
            --cluster "$cluster" --run-specextract --no-run-sherpa \
            --no-specextract-weight --no-specextract-correctpsf \
            2>&1 | grep -E "\[info\]|\[warn\].*spect" || true
    else
        echo "$n_spectra existing spectra, skipping specextract."
    fi

    # Beta-model profile
    beta_json="chandra_data_evt/${cluster}/postprocess_r500_blanksky/${cluster}_beta_model.json"
    if [ ! -f "$beta_json" ]; then
        python src/02_spectral/beta_model_profile.py --cluster "$cluster" 2>&1 | grep "\[info\]" || true
    fi

    # Spectral fitting
    echo "Fitting..."
    python src/02_spectral/fit_spectral_joint.py --cluster "$cluster" 2>&1 \
        | grep -E "T_X|rstat|Abundance|missing|Found|R_EM" || true
done

echo ""
echo "======== BATCH COMPLETE ========"
python src/02_spectral/batch_spectral_joint.py 2>&1 | grep -v "CIAO\|bindir\|CALDB"
