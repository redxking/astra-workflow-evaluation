---
author: Angelis Pseftis
creator: Angelis Pseftis
created: 2026-09-15
---
# Blinded expert review

`blind.py` exports all completed study responses with randomized labels and a separate private unblinding key. It refuses incomplete studies, existing destinations, and keys inside a Git checkout. It strips arm/configuration metadata by selecting only task identity and final response; it does not rewrite the output. The actual task contract and source inputs must be supplied to reviewers separately, with no oracle, model label or automated score.

```sh
python3 validation/review/blind.py --help
```

Prepare two review sheets for two independent domain reviewers. Both score the same outputs without discussing results. Keep the key and model scores hidden until ratings are locked. Record conflicts of interest, access to previous public results and any inference about arm identity. Already-public outputs weaken blinding; use unpublished confirmation outputs for a stronger test. Prepared sheets are not completed reviews or evidence of independence.

## Rubric

Use integer ratings 0–4 for correctness, evidence traceability, edge-case coverage and completeness: 0 fundamentally wrong or missing; 1 major repairs required; 2 material correction required; 3 acceptable with minor changes; 4 meets the task contract without a material defect. Record specific supporting evidence for each material deduction. Apply task-specific anchors and indispensable checks before exposing confirmation outputs, not retrospectively. No aesthetic preference should outweigh a correctness defect.

Record `critical_error` independently of the numerical ratings; examples include an unsafe authorization conclusion, fabricated validation, a broken indispensable invariant or a materially unsupported attribution. Record accept/revise/reject against the frozen task contract. These rubric anchors are a template, not a validated instrument or substitute for domain-specific criteria.

Report raw paired ratings, exact agreement, disagreement severity and an appropriate agreement statistic chosen before scoring. A blinded adjudicator resolves disagreements with written reasons; retain original ratings. Do not quietly average away a critical error. Unblind only after ratings and adjudication are immutable. Model-assisted triage must be disclosed separately and cannot supply human independence.
