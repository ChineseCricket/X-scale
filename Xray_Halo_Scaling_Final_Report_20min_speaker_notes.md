# X-ray Halo Scaling Final Report: 20-minute speaker notes

## Slide 1: Thesis
Open with the project in one sentence: Chandra X-ray measurements are compared to weak-lensing halo masses for CLASH + LoCuSS clusters. State the main result early: mass-based slopes are stable to core excision within current uncertainties, while L_X-T_X is the noisiest relation.

## Slide 2: Talk map
Tell the audience the talk follows one causal chain, not a list of scripts: clusters matter, halo mass sets the potential, gas physics makes X-rays, Chandra spectra measure L_X and T_X, and linmix fits the scaling relations.

## Slide 3: Motivation
Frame clusters as both cosmological objects and plasma laboratories. Weak-lensing M500 is the independent mass anchor, while X-ray observables probe the intracluster medium and its non-gravitational physics.

## Slide 4: Physical chain
Walk through M500 -> potential depth -> gas temperature and density -> X-ray luminosity -> scaling relations. Emphasize that T_X-M500 is closer to gravitational physics, while L_X-M500 is more sensitive to gas density, cores, mergers, and feedback.

## Slide 5: Self-similar theory
Use the equations as a reference model. The point is not that real clusters are perfectly self-similar, but that deviations in slope and intrinsic scatter tell us where baryonic physics and measurement systematics enter.

## Slide 6: Sample
Explain the sample funnel: parent CLASH + LoCuSS clusters, visual/aspheric exclusions, 23 processed clusters, and the 18-cluster exclude_bad sample used for the headline fits.

## Slide 7: Pipeline
Stress the workflow principle: merged imaging is useful for QA and region definition, but spectra must be extracted and modeled per ObsID so that each observation has the correct response files.

## Slide 8: Spectral fitting
This is the technical center of the project. Mention absorbed APEC for ICM emission, blank-sky particle background renormalized at 9.5-12 keV, sky-background components, Sherpa WSTAT, and the QA role of the plotted fit.

## Slide 9: Scaling model
Define the log-linear fixed-evolution model and the pivots. Note the pivot caveat: 3e14 Msun is below the good-only data cloud, so normalization can be extrapolated even when slopes remain stable.

## Slide 10: Full-R500 results
Show the three headline figures. Give the baseline numbers: L_X-M500 beta = 1.08 with 0.169 dex scatter; T_X-M500 beta = 0.48 with 0.117 dex scatter; L_X-T_X beta = 0.76 with 0.227 dex scatter.

## Slide 11: Interpretation
Do not overclaim precision. The main interpretation is relational: temperature is the cleaner mass proxy, luminosity carries more gas-density physics, and L_X-T_X is useful but noisy in this sample.

## Slide 12: Core excision
Core excision removes 0.15 R500 and asks whether central gas dominates the measured trends. The answer here is that the mass-based slopes remain consistent within uncertainties.

## Slide 13: Core-excised figures
Use this as a quick visual confirmation slide. The figures support the same qualitative conclusion as the numeric table.

## Slide 14: Robustness
Explain that bad systems are excluded from the headline relation and retained high/suspect systems are checked by sensitivity fits. Mention that good-only subsets are useful diagnostics but not a replacement headline sample.

## Slide 15: Limitations
Be explicit and calm: the project demonstrates the complete measurement chain, but sample size, heterogeneous selection, background modeling, and outlier sensitivity limit publication-level precision.

## Slide 16: Take-home
Close with the final sentence: Chandra hot-gas observables trace weak-lensing halo mass broadly as expected, but precision is limited by small-sample statistics and background-sensitive spectral modeling.
