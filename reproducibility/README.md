---
author: Angelis Pseftis
creator: Angelis Pseftis
---

# External replication kit

This offline Python 3 standard-library kit checks release bytes and frozen inputs, records minimal local runtime metadata, and prepares or inspects an external replication submission. It does not execute models, contact reviewers, retrieve URLs, transmit submissions, or establish independent replication. A second local agent, blank template, matching hash, or self-reported result is not independent validation.

## Usage

Run from the repository root, using Python 3.9 or newer:

```sh
python3 reproducibility/replicate.py verify --root .
python3 reproducibility/replicate.py environment
python3 reproducibility/replicate.py template --output /chosen/bundle/submission.json
python3 reproducibility/replicate.py inspect --bundle /chosen/bundle
python3 -m unittest discover -s reproducibility/tests -v
```

Create the chosen bundle directory first. The template command refuses to overwrite an existing submission; edit that one authoritative submission in place. The source template remains the reusable blank form, not a draft of the external submission. The README is the kit's sole authored explanatory document. Structured files identify Angelis Pseftis as their author and creator; external reviewer identity and affiliation remain blank until an actual reviewer supplies them.

`verify` prints SHA-256 comparisons for every path explicitly listed in `release-manifest.json`. It also checks both `protocol.json` and `studies/expanded/protocol.json` against the manifest, then verifies each protocol's `files` mapping relative to that protocol's directory. It neither regenerates frozen files nor invokes study scripts. Missing or unreadable inputs are `unknown`; differing hashes are `fail`. An empty mapping cannot pass. The release manifest excludes itself; its observed digest is reported. To check a digest obtained through a separately trusted source, add `--manifest-sha256 YOUR_64_CHARACTER_SHA256`. Without that anchor, byte consistency can pass while manifest authenticity remains unknown. Hash agreement with a locally supplied manifest does not prove a public release's provenance.

Unlisted files are not inspected, included, or represented as published. In particular, locally generated results outside the manifest do not become public evidence because this kit can run beside them. To replicate a published version, first obtain the intended release through your trusted channel, record its commit and manifest digest, and run checks against that checkout. This kit does not fetch or publish a release.

`environment` prints UTC capture time, Python version and implementation, OS family and release, and machine architecture. It reads no authentication files, environment variables, user or host names, private configuration, package inventories, account settings, or CLI state. Model and Codex versions remain null for the reviewer to provide with appropriate evidence. This record characterizes the inspection environment, not an unobserved model execution environment.

## External execution and evidence

An actual external reviewer must decide and document independence, funding or conflicts, release selection, available model/version and configuration, protocol adherence, deviations, and execution dates. Follow the selected study's frozen protocol and execution documentation after reviewing its model-call costs and prerequisites. Preserve all assigned attempts, including failures, and resolve usage explicitly; unknown usage is never zero. Do not silently substitute a model or change frozen inputs. Record any deviation and keep a distinct replication dataset. This kit performs none of those runs.

Fill the submission's nine evidence categories: release integrity, protocol integrity, environment, run records, scoring, usage accounting, timing, deviations, and reviewer independence. Keep unknown fields null or `unknown`. The `reported_status` is a reviewer's assertion, not an inspector finding. For a local evidence file, use `kind: "local_file"`, a bundle-relative `reference`, its exact SHA-256, and a description. For an external link use `kind: "external_url"`; it remains unretrieved and unverified. Do not include credentials or private account files. Review and redact proposed public evidence yourself before placing it in a bundle; this tool does not sanitize arbitrary file contents or package files for release.

`inspect` validates the structure against the supplied schema's implemented subset, distinguishes self-report-only claims from linked local files and unretrieved external links, and verifies local file hashes. Missing files, missing hashes, missing categories, unverifiable URLs, and blank identities never pass. Even every available file matching its digest leaves substantiation, independence, and replication outcome `unknown`: substantive external review must establish source authenticity, relevance, completeness, correct scoring and accounting, and whether results support the claim. The inspector does not infer truth by parsing a file named “pass” or a self-reported status.

Paths must be relative to the supplied root. Traversal, symlinks, URL-shaped local paths, and common credential/configuration paths are rejected before file reads. The tool does not execute submitted code, enumerate private directories, or open linked URLs. Hashing a deliberately supplied public `config/` artifact is allowed; private account configuration is not. Use a deliberately curated release/bundle root, not a home directory. The path filter is a precaution, not content-based secret detection.

Exit status is `0` for complete byte-integrity checks or successful metadata/template generation, `1` for a detected hash mismatch, and `2` for unknown/incomplete inspection or rejected input. Inspection intentionally cannot return an independent-replication pass. JSON output, including `external_manifest_anchor_status`, is authoritative about the scope of any result. No prefilled external submission or reviewer endorsement is included.
