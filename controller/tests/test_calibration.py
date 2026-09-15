"""Tests of statistical boundaries, leakage rejection, and fail-closed routing."""

import copy
import hashlib
import json
import math
import unittest

from controller.calibration import exact_binomial_lower_tail, fit_and_calibrate, select_effort


def row(i, x=.5, low_pass=True, high_pass=True, low_tokens=10, high_tokens=100):
    return {"task_id": str(i), "cluster_id": "cluster-" + str(i), "features": {"x": x},
            "outcomes": {"medium": {"passed": low_pass, "tokens": low_tokens},
                         "high": {"passed": high_pass, "tokens": high_tokens}}}


def rehash(certificate):
    payload = {key: value for key, value in certificate.items() if key != "certificate_hash"}
    certificate["certificate_hash"] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.training = [row("train0", 0), row("train1", 1)]

    def fit(self, rows, **kwargs):
        return fit_and_calibrate(self.training, rows, **kwargs)

    def route(self, cert, features):
        return select_effort(cert, features, fallback_effort="high")

    def test_analytic_binomial_cases(self):
        self.assertEqual(exact_binomial_lower_tail(0, 0, .05), 1)
        self.assertAlmostEqual(exact_binomial_lower_tail(10, 0, .05), .95 ** 10, places=14)
        self.assertAlmostEqual(exact_binomial_lower_tail(4, 1, .5), 5 / 16, places=14)
        self.assertAlmostEqual(exact_binomial_lower_tail(4, 2, .5), 11 / 16, places=14)
        self.assertEqual(exact_binomial_lower_tail(5, 0, 0), 1)
        self.assertEqual(exact_binomial_lower_tail(5, 4, 1), 0)
        self.assertEqual(exact_binomial_lower_tail(5, 5, 1), 1)
        for args in [(-1, 0, .5), (1, 2, .5), (1, 0, float("nan")), (True, 0, .5)]:
            with self.assertRaises(ValueError):
                exact_binomial_lower_tail(*args)

    def test_zero_observed_errors_is_not_zero_risk_certificate(self):
        cert = self.fit([row(i) for i in range(10)])
        cheap = cert["evaluations"][1]
        self.assertEqual(cheap["incremental_failures"], 0)
        self.assertGreater(cheap["p_value"], .5)
        self.assertFalse(cheap["admitted"])
        self.assertEqual(cert["selected_policy_id"], "reference")

    def test_alpha_zero_never_admits_cheap_from_finite_observations(self):
        cert = self.fit([row(i) for i in range(400)], alpha=0)
        self.assertEqual(cert["selected_policy_id"], "reference")
        self.assertTrue(all(not entry["admitted"] for entry in cert["evaluations"][1:]))

    def test_empty_or_insufficient_calibration_falls_back(self):
        for rows in ([], [row(1)]):
            cert = self.fit(rows)
            self.assertEqual(self.route(cert, {"x": .5}), "high")
        empty_training = fit_and_calibrate([], [row(i) for i in range(100)])
        self.assertEqual(empty_training["selected_policy_id"], "reference")

    def test_admissible_cheaper_policy_and_explicit_evidence_boundary(self):
        cert = self.fit([row(i) for i in range(100)], source_data_kind="synthetic_demo")
        self.assertEqual(cert["nonbaseline_family_size"], 3)
        self.assertEqual(cert["selected_policy_id"], "candidate")
        self.assertEqual(self.route(cert, {"x": .5}), "medium")
        self.assertFalse(cert["conditions"]["actual_workload_certification"])
        self.assertFalse(cert["conditions"]["future_savings_guarantee"])
        self.assertEqual(cert["evaluations"][1]["measured_tokens"], 1000)

    def test_paired_loss_is_one_sided_incremental_harm(self):
        rows = [row(i, low_pass=False, high_pass=False) for i in range(100)]
        cert = self.fit(rows)
        self.assertEqual(cert["evaluations"][1]["incremental_failures"], 0)
        # Relative safety does not imply an adequate absolute pass rate.
        self.assertEqual(cert["selected_policy_id"], "candidate")
        rows[0]["outcomes"]["high"]["passed"] = True
        self.assertEqual(self.fit(rows)["evaluations"][1]["incremental_failures"], 1)

    def test_learned_stump_can_beat_rejected_constant(self):
        rows = [row(i, x=0 if i < 100 else 1, low_pass=i < 100) for i in range(200)]
        cert = self.fit(rows)
        self.assertEqual(cert["selected_policy_id"], "stump_1")
        self.assertEqual(self.route(cert, {"x": 0}), "medium")
        self.assertEqual(self.route(cert, {"x": 1}), "high")

    def test_family_preformed_without_calibration_labels_or_features(self):
        first = self.fit([row(i, x=.2) for i in range(100)])
        second = self.fit([row(i, x=.9, low_pass=False) for i in range(100)])
        self.assertEqual(first["policy_family"], second["policy_family"])
        self.assertEqual(first["hashes"]["policy_family"], second["hashes"]["policy_family"])
        self.assertNotEqual(first["hashes"]["calibration_data"], second["hashes"]["calibration_data"])

    def test_family_is_bounded_and_canonical_hashes_ignore_row_order(self):
        training = [row("t" + str(i), i) for i in range(200)]
        cert = fit_and_calibrate(training, [row(0)])
        self.assertLessEqual(len(cert["policy_family"]), 100)
        reverse = fit_and_calibrate(list(reversed(training)), [row(0)])
        self.assertEqual(cert["certificate_hash"], reverse["certificate_hash"])

    def test_leakage_and_calibration_pseudoreplication_rejected(self):
        same_cluster = row("other")
        same_cluster["cluster_id"] = self.training[0]["cluster_id"]
        duplicate_cluster = row(2)
        duplicate_cluster["cluster_id"] = row(1)["cluster_id"]
        for rows in ([self.training[0]], [same_cluster], [row(1), row(1)],
                     [row(1), duplicate_cluster]):
            with self.assertRaises(ValueError):
                self.fit(rows)

    def test_unknown_or_invalid_measurements_refused(self):
        for value in (None, True, -1, 1.0, float("nan"), "10"):
            invalid = row(1)
            invalid["outcomes"]["medium"]["tokens"] = value
            with self.assertRaises(ValueError):
                self.fit([invalid])
        for value in (1, None, "true"):
            invalid = row(1)
            invalid["outcomes"]["high"]["passed"] = value
            with self.assertRaises(ValueError):
                self.fit([invalid])
        for value in (True, float("nan"), float("inf"), "1"):
            with self.assertRaises(ValueError):
                self.fit([row(1, x=value)])

    def test_out_of_domain_input_and_calibration_routing_fail_closed(self):
        cert = self.fit([row(i) for i in range(100)])
        for features in ({}, {"z": 0}, {"x": .5, "z": 0}, {"x": 2},
                         {"x": -.1}, {"x": float("nan")}, {"x": True}, None):
            self.assertEqual(self.route(cert, features), "high")
        outside = self.fit([row(i, x=2, low_pass=False) for i in range(100)])
        self.assertEqual(outside["evaluations"][1]["candidate_routes"], 0)
        self.assertEqual(outside["selected_policy_id"], "reference")

    def test_tampered_certificate_uses_externally_trusted_fallback(self):
        cert = self.fit([row(i) for i in range(100)])
        tampered = copy.deepcopy(cert)
        tampered["reference_effort"] = "ultra"
        self.assertEqual(self.route(tampered, {"x": .5}), "high")
        for value in (None, {}, [], {"reference_effort": "low"}):
            self.assertEqual(self.route(value, {"x": .5}), "high")
        # A certificate for a different reference cannot override caller policy.
        self.assertEqual(select_effort(cert, {"x": .5}), "medium")

    def test_even_rehashed_inconsistent_admission_or_measurements_fail_closed(self):
        cert = self.fit([row(i) for i in range(10)])
        tampered = copy.deepcopy(cert)
        tampered["selected_policy_id"] = "candidate"
        tampered["evaluations"][1]["admitted"] = True
        rehash(tampered)
        self.assertEqual(self.route(tampered, {"x": .5}), "high")
        cert = self.fit([row(i) for i in range(100)])
        for mutation in (lambda c: c.update(measurement="estimated_tokens"),
                         lambda c: c["evaluations"][1].update(measured_tokens=None)):
            tampered = copy.deepcopy(cert)
            mutation(tampered)
            rehash(tampered)
            self.assertEqual(self.route(tampered, {"x": .5}), "high")

    def test_cheaper_selection_is_only_among_admitted_and_baseline(self):
        cert = self.fit([row(i, low_tokens=200) for i in range(100)])
        self.assertTrue(cert["evaluations"][1]["admitted"])
        self.assertEqual(cert["selected_policy_id"], "reference")


if __name__ == "__main__":
    unittest.main()

class ReviewRegressionTests(unittest.TestCase):
    def test_subnormal_delta_rejected(self):
        with self.assertRaises(ValueError):
            fit_and_calibrate([row('train')],[row('cal')],delta=math.ulp(0.0))
    def test_enormous_certificate_count_falls_back(self):
        cert=fit_and_calibrate([row('train')],[row('cal')])
        cert['calibration_count']=10**9
        for entry in cert['evaluations']:
            entry['n']=10**9
            if entry['policy_id']!='reference':
                entry['incremental_failures']=5*10**8
                entry['candidate_routes']=5*10**8
        rehash(cert)
        self.assertEqual(select_effort(cert,{'x':.5},fallback_effort='high'),'high')
