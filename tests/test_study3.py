import unittest
from pathlib import Path

import numpy as np

from injection_lab.study3 import (
    N_TRAIN,
    N_VAL,
    assert_outside_repo,
    f1_at,
    feasible_counts,
    fingerprint,
    joint_bootstrap_diff,
    largest_remainder,
    percentile_interval,
    sample_pool,
    seed_t_interval,
    semantic_keep_mask,
    sweep_frontier,
    to_hardneg_frame_rows,
)


def fake_cells(sizes):
    return {
        cell: [
            {"text": f"{cell} prompt number {i}", "source": cell.split("|")[0]} for i in range(n)
        ]
        for cell, n in sizes.items()
    }


class AllocationTests(unittest.TestCase):
    def test_largest_remainder_sums_and_is_proportional(self):
        weights = {"a": 298, "b": 366, "c": 40, "d": 100, "e": 18, "f": 50}
        out = largest_remainder(weights, 535)
        self.assertEqual(sum(out.values()), 535)
        for k, w in weights.items():
            self.assertLessEqual(abs(out[k] - w / 872 * 535), 1)

    def test_feasible_counts_moves_deficit_to_fallback(self):
        counts, moved = feasible_counts(
            {"lmsys|k": 298, "dolly|k": 18},
            {"lmsys|k": 1000, "dolly|k": 3},
            535,
            {"dolly|k": "lmsys|k"},
        )
        self.assertEqual(counts["dolly|k"], 3)
        self.assertEqual(sum(counts.values()), 535)
        self.assertEqual(
            moved,
            {"dolly|k": largest_remainder({"lmsys|k": 298, "dolly|k": 18}, 535)["dolly|k"] - 3},
        )

    def test_feasible_counts_without_fallback_raises(self):
        with self.assertRaises(ValueError):
            feasible_counts({"a": 1, "b": 1}, {"a": 1, "b": 1000}, 10, {})


class PoolTests(unittest.TestCase):
    def test_sample_pool_sizes_composition_and_disjointness(self):
        weights = {"lmsys|keyword": 298, "lmsys|random": 366, "dolly|keyword": 18}
        cells = fake_cells({k: 600 for k in weights})
        train, val = sample_pool(cells, weights)
        self.assertEqual((len(train), len(val)), (N_TRAIN, N_VAL))
        self.assertFalse({r["text"] for r in train} & {r["text"] for r in val})
        total = largest_remainder(weights, N_TRAIN + N_VAL)
        for cell, n in total.items():
            self.assertEqual(sum(r["cell"] == cell for r in train + val), n)

    def test_sample_pool_is_deterministic_and_order_invariant(self):
        weights = {"x|keyword": 1, "y|random": 1}
        cells = fake_cells({k: 400 for k in weights})
        shuffled = {k: list(reversed(v)) for k, v in cells.items()}
        self.assertEqual(sample_pool(cells, weights), sample_pool(shuffled, weights))

    def test_sample_pool_raises_when_cell_too_small(self):
        with self.assertRaises(ValueError):
            sample_pool(fake_cells({"a|k": 10, "b|k": 1000}), {"a|k": 1, "b|k": 1})

    def test_hardneg_rows_match_pidsbench_schema(self):
        rows = to_hardneg_frame_rows(
            [{"text": "hi there", "source": "dolly", "cell": "dolly|keyword"}], "A2", "train"
        )
        self.assertEqual(
            list(rows[0]),
            [
                "text",
                "label",
                "source_type",
                "parent_seed_id",
                "split",
                "hardneg_category",
                "source",
                "attack_type",
                "language",
                "obfuscation",
            ],
        )
        self.assertEqual(rows[0]["label"], 0)
        self.assertEqual(fingerprint("A  b"), fingerprint("a b"))


class DedupTests(unittest.TestCase):
    def test_semantic_mask_drops_near_copies_only(self):
        refs = ["How do I reset my router password safely at home?"]
        cands = [
            "how do I reset  my router password safely at home?",
            "Write a haiku about autumn leaves.",
        ]
        self.assertEqual(semantic_keep_mask(cands, refs).tolist(), [False, True])

    def test_assert_outside_repo(self):
        repo = Path(__file__).resolve().parents[1]
        with self.assertRaises(PermissionError):
            assert_outside_repo(repo / "data" / "x.csv", repo)
        self.assertEqual(assert_outside_repo("/content/x", repo), Path("/content/x").resolve())


class InferenceTests(unittest.TestCase):
    def test_identical_arms_give_zero_difference(self):
        rng = np.random.default_rng(0)
        flags = rng.integers(0, 2, size=(5, 50))
        groups = np.repeat(np.arange(25), 2)
        reps = joint_bootstrap_diff(flags, flags, groups, 300, np.random.default_rng(1))
        self.assertTrue(np.allclose(reps, 0))

    def test_constant_shift_is_recovered(self):
        a = np.ones((5, 40))
        b = np.zeros((5, 40))
        b[:, :10] = 1  # rate 0.25
        reps = joint_bootstrap_diff(a, b, np.arange(40), 500, np.random.default_rng(2))
        lo, hi = percentile_interval(reps, 0.95)
        self.assertLess(lo, 0.75)
        self.assertGreater(hi, 0.75)
        self.assertGreater(lo, 0.5)

    def test_seed_t_interval_matches_hand_value(self):
        lo, hi = seed_t_interval([0.0, 0.1, 0.2, 0.1, 0.1], 0.95)
        half = 2.7764451 * np.std([0.0, 0.1, 0.2, 0.1, 0.1], ddof=1) / np.sqrt(5)
        self.assertAlmostEqual(lo, 0.1 - half, places=6)
        self.assertAlmostEqual(hi, 0.1 + half, places=6)

    def test_f1_and_frontier(self):
        y = np.array([1, 1, 0, 0])
        s = np.array([0.9, 0.8, 0.1, 0.2])
        self.assertEqual(f1_at(s, y, 0.5), 1.0)
        self.assertTrue(sweep_frontier(s, y, np.array([0.1, 0.3])))
        self.assertFalse(sweep_frontier(s, y, np.array([0.95, 0.99])))


if __name__ == "__main__":
    unittest.main()
