"""Offline paired-risk calibration for a finite, training-only policy family.

The binomial test is finite-sample (not a normal approximation). Its validity
requires independent, representative calibration clusters and stationary labels;
this module cannot establish those conditions. Digests detect accidental changes,
not adversarial replacement or provenance. No model or global configuration is used.
"""

import hashlib
import json
import math


SCHEMA_VERSION = 1
MAX_FAMILY_SIZE = 100


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _finite(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _validate_rows(rows, reference, candidate, *, calibration):
    if not isinstance(rows, (list, tuple)):
        raise ValueError("Rows must be a list or tuple of fully measured paired outcomes")
    validated = []
    tasks, clusters = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each row must be an object")
        task, cluster = row.get("task_id"), row.get("cluster_id")
        if not isinstance(task, str) or not task or not isinstance(cluster, str) or not cluster:
            raise ValueError("Nonempty task_id and cluster_id strings are required")
        if task in tasks:
            raise ValueError("Repeated task_id")
        if calibration and cluster in clusters:
            raise ValueError("Calibration requires one independent row per cluster")
        tasks.add(task)
        clusters.add(cluster)
        features, outcomes = row.get("features"), row.get("outcomes")
        if not isinstance(features, dict) or any(
            not isinstance(key, str) or not key or not _finite(value)
            for key, value in features.items()
        ):
            raise ValueError("Features must have nonempty names and finite numeric values")
        if not isinstance(outcomes, dict):
            raise ValueError("Paired outcomes are required")
        clean_outcomes = {}
        for effort in (reference, candidate):
            outcome = outcomes.get(effort)
            if not isinstance(outcome, dict) or type(outcome.get("passed")) is not bool:
                raise ValueError("Both effort outcomes require strict boolean passed labels")
            tokens = outcome.get("tokens")
            if type(tokens) is not int or tokens < 0:
                raise ValueError("Unknown or noninteger token measurements are refused")
            clean_outcomes[effort] = {"passed": outcome["passed"], "tokens": tokens}
        validated.append({"task_id": task, "cluster_id": cluster,
                          "features": dict(features), "outcomes": clean_outcomes})
    return sorted(validated, key=lambda row: row["task_id"]), tasks, clusters


def _learn_family(training):
    baseline = {"id": "reference", "kind": "reference"}
    if not training:
        return [baseline], {}
    names = sorted(training[0]["features"])
    if any(set(row["features"]) != set(names) for row in training):
        raise ValueError("Training rows must have the same feature names")
    bounds = {name: {"min": min(row["features"][name] for row in training),
                     "max": max(row["features"][name] for row in training)}
              for name in names}
    family = [baseline, {"id": "candidate", "kind": "candidate"}]
    for name in names:
        values = sorted({row["features"][name] for row in training})
        for left, right in zip(values, values[1:]):
            # Halving first avoids overflow for large finite endpoints.
            threshold = left / 2 + right / 2
            if not _finite(threshold):
                continue
            for direction in ("le", "gt"):
                if len(family) >= MAX_FAMILY_SIZE:
                    return family, bounds
                family.append({"id": "stump_" + str(len(family) - 1),
                               "kind": "stump", "feature": name,
                               "threshold": threshold, "direction": direction})
    return family, bounds


def _features_in_domain(features, bounds):
    return (isinstance(features, dict) and set(features) == set(bounds)
            and all(_finite(value) and bounds[name]["min"] <= value <= bounds[name]["max"]
                    for name, value in features.items()))


def _route(policy, features, bounds, reference, candidate):
    if not _features_in_domain(features, bounds):
        return reference
    if policy["kind"] == "reference":
        return reference
    if policy["kind"] == "candidate":
        return candidate
    low = features[policy["feature"]] <= policy["threshold"]
    if policy["direction"] == "gt":
        low = not low
    return candidate if low else reference


def exact_binomial_lower_tail(n, k, probability):
    """Return P[Binomial(n, probability) <= k], without asymptotics."""
    if type(n) is not int or type(k) is not int or n < 0 or not 0 <= k <= n:
        raise ValueError("Require integer 0 <= k <= n")
    if not _finite(probability) or not 0 <= probability <= 1:
        raise ValueError("Probability must be finite and in [0, 1]")
    if k == n or probability == 0:
        return 1.0
    if probability == 1:
        return 0.0
    log_p = math.log(probability)
    log_q = math.log1p(-probability)
    terms = [math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1)
             + j * log_p + (n - j) * log_q for j in range(k + 1)]
    largest = max(terms)
    result = math.exp(largest) * math.fsum(math.exp(term - largest) for term in terms)
    return min(1.0, max(0.0, result))


def fit_and_calibrate(training_rows, calibration_rows, *, reference_effort="high",
                      candidate_effort="medium", alpha=.05, delta=.05,
                      source_data_kind="unspecified"):
    """Build a conditional statistical certificate from separate measured datasets.

    L is one only when the reference passes and the routed policy fails. Tests
    reject H0: E[L] >= alpha using a Bonferroni correction over the preformed
    nonreference family. Savings are empirical calibration-set quantities only.
    """
    if (not isinstance(reference_effort, str) or not reference_effort
            or not isinstance(candidate_effort, str) or not candidate_effort
            or reference_effort == candidate_effort):
        raise ValueError("Distinct nonempty effort names are required")
    if not _finite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("alpha must be in [0, 1]")
    if not _finite(delta) or not 1e-12 <= delta < 1:
        raise ValueError("delta must be in [1e-12, 1)")
    if source_data_kind not in ("observed", "synthetic_demo", "unspecified"):
        raise ValueError("source_data_kind must be observed, synthetic_demo, or unspecified")
    training, train_tasks, train_clusters = _validate_rows(
        training_rows, reference_effort, candidate_effort, calibration=False)
    if len(calibration_rows)>100000:raise ValueError('At most 100000 calibration rows supported')
    calibration, cal_tasks, cal_clusters = _validate_rows(
        calibration_rows, reference_effort, candidate_effort, calibration=True)
    if train_tasks & cal_tasks or train_clusters & cal_clusters:
        raise ValueError("Training and calibration task IDs AND cluster IDs must be disjoint")
    # Candidates are generated exclusively from training data, before calibration.
    family, bounds = _learn_family(training)
    multiplicity = len(family) - 1
    threshold = delta / multiplicity if multiplicity else None
    evaluations = []
    for policy in family:
        losses = tokens = candidate_routes = 0
        for row in calibration:
            effort = _route(policy, row["features"], bounds, reference_effort, candidate_effort)
            reference = row["outcomes"][reference_effort]
            chosen = row["outcomes"][effort]
            losses += int(reference["passed"] and not chosen["passed"])
            tokens += chosen["tokens"]
            candidate_routes += int(effort == candidate_effort)
        baseline = policy["kind"] == "reference"
        p_value = None if baseline else exact_binomial_lower_tail(len(calibration), losses, alpha)
        admitted = baseline or bool(alpha > 0 and calibration and p_value <= threshold)
        evaluations.append({"policy_id": policy["id"], "n": len(calibration),
                            "incremental_failures": losses, "p_value": p_value,
                            "bonferroni_threshold": None if baseline else threshold,
                            "admitted": admitted, "measured_tokens": tokens,
                            "candidate_routes": candidate_routes})
    eligible = [entry for entry in evaluations if entry["admitted"]]
    selected = min(eligible, key=lambda entry: (entry["measured_tokens"],
                                               entry["policy_id"] != "reference",
                                               entry["policy_id"]))
    certificate = {
        "schema_version": SCHEMA_VERSION, "reference_effort": reference_effort,
        "candidate_effort": candidate_effort, "alpha": alpha, "delta": delta,
        "data_kind": source_data_kind,
        "measurement": "strict_observed_integer_tokens", "feature_bounds": bounds,
        "policy_family": family, "nonbaseline_family_size": multiplicity,
        "training_count": len(training), "calibration_count": len(calibration),
        "hashes": {"training_data": _digest(training), "calibration_data": _digest(calibration),
                   "policy_family": _digest(family)},
        "evaluations": evaluations, "selected_policy_id": selected["policy_id"],
        "conditions": {
            "iid_representative_calibration_clusters": "unverified_required_assumption",
            "labeling_and_workload_stationarity": "unverified_required_assumption",
            "independent_cluster_identifiers": "user_supplied_not_independently_verified",
            "actual_workload_certification": False,
            "cost_optimality": "observed_calibration_tokens_among_admitted_family_only",
            "future_savings_guarantee": False,
            "integrity": "unkeyed_sha256_change_detection_not_authentication",
        },
        "risk_definition": "P(reference_passes_and_routed_policy_fails)",
        "fallback": "reference_relative_incremental_risk_is_zero_by_construction",
    }
    certificate["certificate_hash"] = _digest(certificate)
    return certificate


def _validate_certificate(certificate):
    if not isinstance(certificate, dict):
        return False
    payload = {key: value for key, value in certificate.items() if key != "certificate_hash"}
    if certificate.get("certificate_hash") != _digest(payload):
        return False
    if (certificate.get("schema_version") != SCHEMA_VERSION
            or certificate.get("measurement") != "strict_observed_integer_tokens"
            or certificate.get("data_kind") not in ("observed", "synthetic_demo", "unspecified")):
        return False
    hashes = certificate["hashes"]
    if not isinstance(hashes, dict) or set(hashes) != {"training_data", "calibration_data", "policy_family"}:
        return False
    if any(not isinstance(value, str) or len(value) != 64
           or any(char not in "0123456789abcdef" for char in value)
           for value in hashes.values()):
        return False
    conditions = certificate["conditions"]
    if (not isinstance(conditions, dict)
            or conditions.get("actual_workload_certification") is not False
            or conditions.get("future_savings_guarantee") is not False
            or conditions.get("iid_representative_calibration_clusters") != "unverified_required_assumption"
            or conditions.get("labeling_and_workload_stationarity") != "unverified_required_assumption"):
        return False
    ref, low = certificate["reference_effort"], certificate["candidate_effort"]
    if not isinstance(ref, str) or not ref or not isinstance(low, str) or not low or ref == low:
        return False
    alpha, delta = certificate["alpha"], certificate["delta"]
    if not _finite(alpha) or not 0 <= alpha <= 1 or not _finite(delta) or not 1e-12 <= delta < 1:
        return False
    bounds = certificate["feature_bounds"]
    if not isinstance(bounds, dict) or any(
        not isinstance(name, str) or not name or not isinstance(bound, dict)
        or set(bound) != {"min", "max"} or not _finite(bound["min"])
        or not _finite(bound["max"]) or bound["min"] > bound["max"]
        for name, bound in bounds.items()
    ):
        return False
    family = certificate["policy_family"]
    if not isinstance(family, list) or not 1 <= len(family) <= MAX_FAMILY_SIZE:
        return False
    if family[0] != {"id": "reference", "kind": "reference"}:
        return False
    if certificate["hashes"]["policy_family"] != _digest(family):
        return False
    identifiers = set()
    for index, policy in enumerate(family):
        if not isinstance(policy, dict) or not isinstance(policy.get("id"), str):
            return False
        if policy["id"] in identifiers:
            return False
        identifiers.add(policy["id"])
        if index == 0:
            continue
        if policy["kind"] == "candidate":
            if policy != {"id": "candidate", "kind": "candidate"}:
                return False
        elif policy["kind"] == "stump":
            if (set(policy) != {"id", "kind", "feature", "threshold", "direction"}
                    or policy["feature"] not in bounds or not _finite(policy["threshold"])
                    or policy["direction"] not in ("le", "gt")
                    or not bounds[policy["feature"]]["min"] <= policy["threshold"] <= bounds[policy["feature"]]["max"]):
                return False
        else:
            return False
    m, n = len(family) - 1, certificate["calibration_count"]
    if (type(n) is not int or n < 0 or certificate["nonbaseline_family_size"] != m
            or type(certificate["training_count"]) is not int or certificate["training_count"] < 0):
        return False
    entries = certificate["evaluations"]
    if not isinstance(entries, list) or len(entries) != len(family):
        return False
    for policy, entry in zip(family, entries):
        if not isinstance(entry, dict) or entry["policy_id"] != policy["id"] or entry["n"] != n:
            return False
        k, tokens, routes = entry["incremental_failures"], entry["measured_tokens"], entry["candidate_routes"]
        if (type(k) is not int or not 0 <= k <= n or n > 100000 or type(tokens) is not int or tokens < 0
                or type(routes) is not int or not 0 <= routes <= n or k > routes
                or type(entry["admitted"]) is not bool):
            return False
        if policy["kind"] == "reference":
            if k != 0 or routes != 0 or not entry["admitted"] or entry["p_value"] is not None or entry["bonferroni_threshold"] is not None:
                return False
        else:
            p = exact_binomial_lower_tail(n, k, alpha)
            if (entry["p_value"] != p or entry["bonferroni_threshold"] != delta / m
                    or entry["admitted"] != bool(alpha > 0 and n > 0 and p <= delta / m)):
                return False
    eligible = [entry for entry in entries if entry["admitted"]]
    selected = min(eligible, key=lambda entry: (entry["measured_tokens"],
                                               entry["policy_id"] != "reference", entry["policy_id"]))
    return certificate["selected_policy_id"] == selected["policy_id"]


def select_effort(certificate, features, *, fallback_effort="medium"):
    """Route only an intact, internally consistent certificate and in-domain input.

    The caller supplies its trusted reference effort; the certificate must match
    it. Never derive a failure fallback from untrusted certificate contents.
    This is integrity checking, not authentication.
    """
    if not isinstance(fallback_effort, str) or not fallback_effort:
        raise ValueError("A nonempty externally trusted fallback_effort is required")
    reference = fallback_effort
    try:
        if not _validate_certificate(certificate) or certificate["reference_effort"] != reference:
            return reference
        policy = next(policy for policy in certificate["policy_family"]
                      if policy["id"] == certificate["selected_policy_id"])
        return _route(policy, features, certificate["feature_bounds"], reference,
                      certificate["candidate_effort"])
    except (ValueError, TypeError, KeyError, OverflowError, StopIteration, RecursionError):
        return reference
