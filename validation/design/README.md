---
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
---
# Confirmation design planning

This directory supplies planning sensitivity calculations, not a frozen confirmatory sample size or evidence of noninferiority. The existing 108-run synthetic protocol remains unchanged.

`precision.py` illustrates a paired-binary normal approximation under an assumed true acceptance difference of zero. Let D = candidate acceptance minus comparator acceptance, and q = P(D differs from zero). Then Var(D)=q under that assumption. The illustrative task-pair count is ceil((z(1-alpha)+z(power))² q / margin²). The script also exposes a heuristic cluster design effect 1+(mean cluster size−1)rho; this is not a validated replacement for simulation of the intended repository/task design.

For a five-percentage-point margin, one-sided alpha .05 and power .8, the supplied q=.05/.10/.20/.40 scenarios yield the counts in `planning-sensitivity.json`. Those assumptions are hypothetical. The script explicitly refuses q=0 rather than interpreting a perfect small pilot as zero required sample size. It does not implement an exact paired-binary noninferiority test, finite-sample correction, equivalence test, multiple-comparison adjustment, or a claim about all work. Pair-matched binary sample-size methods depend on discordance and finite-sample choices; see [Royston's primary methods paper](https://pubmed.ncbi.nlm.nih.gov/8511446/).

Before committing model runs:

1. Define a target workload and explicit acceptance endpoint, including critical-error vetoes. Keep software repair, structured evidence work, and open-ended writing as separate strata or studies.
2. Establish an eligible task frame and license boundaries. Cluster related tasks by repository and task family; tuning and confirmation must not share clusters when claiming out-of-project generalization.
3. Freeze grading rubrics and independent reviewer arrangements for subjective outcomes. Do not assume the study author or another locally operated model supplies independence.
4. Estimate plausible discordance and correlation from a representative calibration set; use conservative sensitivity cases when estimates are unstable. Simulate the selected inference method under null and alternative conditions before freezing sample size.
5. Predefine one primary comparator and endpoint. Comparing against both Medium and Ultra, multiple quality dimensions, and multiple speed/cost endpoints requires an explicit multiplicity strategy or clearly exploratory secondary claims.
6. Balance all six arm-order permutations across tasks, block by execution window, and repeat across days. Cache telemetry records observed state; no cold-cache or provider-control claim without verified controls.
7. Separate algorithm/mechanism ablations from whole-workflow comparisons. Include routing, failed attempts, verification and human repair in resource accounting; do not equate subscription tokens with dollars.
8. Freeze the exact task list, provenance, policy, environment, sample size, statistical procedure, exclusion policy and stopping rule before confirmation outcomes are observed. Publish adverse and inconclusive outcomes.

No confirmation-sized model batch is launched by this planning tool. It prevents a convenient task count from being mistaken for a statistically justified one.
