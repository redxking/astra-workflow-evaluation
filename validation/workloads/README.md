# Software-repair workload candidate inventory

Author: Angelis Pseftis

This inventory contains metadata for all 500 SWE-bench Verified test instances from 12 Python repositories, pinned to Hugging Face revision `c104f840cc67f8b6eec6f759ebc8b2693d585d4a`. It is a real public software-repair candidate frame for a future study. No model, harness, Docker image, or paid API was run. Every instance is marked execution-ineligible pending the listed gates. Metadata completeness is not operational validation.

## Sources and attribution

The [official SWE-bench documentation](https://www.swebench.com/SWE-bench/) identifies GitHub issue resolution as the benchmark task. The [pinned dataset card](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/blob/c104f840cc67f8b6eec6f759ebc8b2693d585d4a/README.md) describes 500 human-validated Issue–Pull Request pairs. Its schema includes solution patches and test patches despite a prose statement that the dataset only contains the problem statement and base commit. This intake follows the actual schema and projects only approved metadata columns.

Original benchmark attribution: Carlos E Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, and Karthik R Narasimhan; *SWE-bench: Can Language Models Resolve Real-world GitHub Issues?* (ICLR 2024). These authors retain attribution for their work. Angelis Pseftis is the author of this inventory documentation and sampling code, not the underlying benchmark, GitHub issues, or repositories.

`provenance.json` records URLs, dataset and harness revisions, source hashes, retrieval time, source counts, and the index hash. The downloaded Parquet source was 2,096,679 bytes, SHA-256 `a45b1fe4e2f0c8390b2b2938ac83e92ed5979000856808f3679c07812e9e6dcd`. Raw intake remains outside this package under local `work/workload-intake`; that area is not a secured vault and must not be distributed or included in model contexts. The distributed index contains identifiers, repository/base-commit references, source version, clustering and eligibility metadata only. It excludes issue prose, hints, gold patches, test patches, and expected-test lists.

## License boundary

The pinned Hugging Face card and retrieved dataset API contain no explicit dataset-license declaration. That is an unresolved clearance issue, not evidence of permission or prohibition. The SWE-bench harness [MIT license at its pinned commit](https://github.com/SWE-bench/SWE-bench/blob/02e7a74ffd0b707aab73d203fe87bdc7c76afc8e/LICENSE) is preserved verbatim in `THIRD_PARTY_HARNESS_LICENSE.txt`, including original copyright holders. This notice does not establish rights for the dataset or underlying repository code. The package's own license must not be read as relicensing third-party material. Only bibliographic/reference metadata is included here; no corpus/code redistribution clearance is claimed. Clear the dataset and relevant repository licenses before acquiring execution inputs or distributing any such content.

## Deterministic proposed sampling design

`sample_workloads.py` uses SHA-256 ranks keyed by seed `20260915`. Whole repositories are assigned before instance selection. Repository size strata are small (1–10 instances), medium (11–50), and large (>50); within each stratum approximately one third of repository clusters are assigned to the proposed confirmatory arm. Rounding preserves at least one cluster per arm where there are two or more clusters; singleton strata stay in tuning. Rows are then sampled within each repository and source-provided difficulty category, capped at three instances per category. These difficulty labels are source annotations, not measured execution times in this study. Stable ordering makes output independent of input ordering and Python hash randomization.

The saved plan assigns 382 instances in eight repositories to `train_tuning` and 118 instances in four repositories to `confirmatory`; 55 and 29 respectively are selected (84 total). Confirmatory repositories are `mwaskom/seaborn`, `pydata/xarray`, `pytest-dev/pytest`, and `sympy/sympy`. The tuning label describes study development/configuration use; no model training occurred. The sample is deliberately stratified and disproportionate; an unweighted success rate does not estimate the 500-instance frame rate. Repo sizes are highly unequal, and the proposed confirmatory arm has only four independent repository clusters.

Run offline from this directory:

```sh
python3 sample_workloads.py --output sample-plan.json
python3 -m unittest discover -s . -p 'test_*.py' -v
```

Seven tests passed: frame identity/schema/hash, duplicate and sensitive-column rejection, seed determinism and order invariance, seed sensitivity, repository isolation and stratum coverage, per-category cap, exact saved-plan reproduction, and ineligible/singleton behavior. Tests verify metadata and the sampling algorithm only; they do not verify executable environments, issue solvability, or model performance.

## Scope and prospective gates

This is a known public benchmark. Repository separation prevents same-repository leakage between this design's arms; it does not remove pretraining exposure, public solutions, benchmark-specific optimization, cross-project similarity, or shared-dependency effects. The proposed confirmatory arm is not an uncontaminated or newly collected held-out corpus. Model training exposure is unknown. No empirical claim about writing, security analysis, engineering planning, other languages, or the user's full workload population is supported by this inventory.

Before a confirmatory run: resolve licenses, independently screen task/environment feasibility without exposing reference answers to evaluated systems, freeze the prospective protocol and selection, establish harness/test access isolation, define environment and cost budgets, and preregister handling of exclusions and failures. Do not redraw the seed after observing results. Do not silently substitute excluded tasks. If a general-workflow claim is desired, collect distinct source-grounded writing and security-analysis frames with their own eligibility and evidence rules. Results from this frame can support only a bounded public Python issue-repair claim.
