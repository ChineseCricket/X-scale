

*Xiaoyang WEI, Jingyi ZHANG*

## Objective

Build a sample of more than 20 bright galaxy groups and clusters with archival **Chandra** and/or **XMM-Newton** observations, together with **non-X-ray $M_{500}$** measurements, and derive:
- X-ray imaging and morphology
- X-ray temperature $T_X$
- X-ray luminosity $L_X$
- basic galaxy properties
- scaling relations, especially $L_X$-$M_{500}$ and $T_X$-$M_{500}$

## Scientific strategy
The project will use **archival X-ray data** to measure imaging, morphology, global temperature, and luminosity, while using **published halo masses independent of X-ray data** to avoid circularity in the $L_X$-mass relation. The preferred independent mass hierarchy is:
1. weak-lensing $M_{500}$
2. SZ-based $M_{500}$
3. richness-based $M_{500}$

All halo masses will be standardized to **$M_{500}$** where possible.

## Sample definition
A parent list of 35–45 nearby bright groups/clusters will be assembled, with a final clean sample of **20–30 systems**. Selection criteria:
- archival Chandra and/or XMM-Newton observations
- sufficient X-ray counts for imaging and a global spectral fit
- published non-X-ray $M_{500}$
- accessible galaxy-property information

The sample will span both **groups** and **clusters** to provide dynamic range in mass and temperature.

## Measurements

### X-ray imaging and morphology
For each target:
- cleaned and exposure-corrected image
- smoothed image for visualization
- point-source masking
- Morphology: measure luminosity in some specific radius

### X-ray spectral analysis
For each target:
- extract a global spectrum
- fit an absorbed thermal plasma model (e.g. `phabs*apec`)
- derive:
  - $T_X$
  - flux
  - $L_X$ in a consistent aperture and band
- if feasible, measure both:
  - core-included luminosity
  - core-excised luminosity

## Scaling relations
The primary scaling relations will be:
- $L_X$ vs. $M_{500}$
- $T_X$ vs. $M_{500}$ 

Relations will be fit in log space, with scatter estimated and subsamples compared where possible.

## Timeline

### Weeks 1–2: sample construction
- define measurement choices and success criteria
- compile parent candidate list
- gather published independent $M_{500}$
- inventory Chandra/XMM observations
- compute $R_{500}$ and apertures
- freeze final sample (>20 systems)

**Deliverable:** final sample table with metadata, masses, observations, and aperture definitions

### Weeks 3–5: X-ray reduction and measurement
- reduce Chandra and XMM data
- produce imaging products
- extract and fit spectra
- measure $T_X$ and $L_X$

**Deliverable:** final science table containing $M_{500}$, $R_{500}$, $T_X$, $L_X$, morphology, and galaxy properties

### Week 6: fitting and summary
- fit scaling relations
- generate figures
- summarize methods, results, caveats, and next steps

**Deliverable:** final plots, fitted relations, and a one-page report / summary slide set

## Expected outputs
1. Final sample of >20 systems with independent $M_{500}$
2. X-ray image products and morphology catalog
3. Spectral measurements of $T_X$ and $L_X$
5. Scaling-relation fits and diagnostic plots
6. Summary document describing methods, results, and limitations

## Reference

- Galaxy cluster X-ray luminosity scaling relations from a representative local sample (REXCESS) https://arxiv.org/pdf/0809.3784
- THE MASS FUNCTION OF AN X-RAY FLUXÈLIMITED SAMPLE OF GALAXY CLUSTERS https://astro.uni-bonn.de/~reiprich/act/gcs/ApJ_567_716.pdf

- The observed growth of massive galaxy clusters - II. X-ray scaling relations https://ui.adsabs.harvard.edu/abs/2010MNRAS.406.1773M/abstract
- The eROSITA Final Equatorial-Depth Survey (eFEDS). X-ray observable-to-mass-and-redshift relations of galaxy clusters and groups with weak-lensing mass calibration from the Hyper Suprime-Cam Subaru Strategic Program survey https://ui.adsabs.harvard.edu/abs/2022A%26A...661A..11C/abstract