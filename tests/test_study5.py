import unittest

import numpy as np

from injection_lab.study5 import (
    FRAMING_CELLS,
    boot_p_noninferior,
    boot_p_two_sided,
    framed,
    holm,
    is_english,
    paired_within_model_diff,
    paraphrase_valid,
    parse_seed_id,
    percentile,
    system_prompt_key,
    twoway_cell_diff,
    unpaired_bootstrap_diff,
    unpaired_bootstrap_interaction,
    welch_interval,
)


class HelperTests(unittest.TestCase):
    def test_parse_seed_id(self):
        self.assertEqual(parse_seed_id("spml_injection_seed_0007792"), ("spml_injection", 7792))
        self.assertIsNone(parse_seed_id("template_seed_0001"))
        self.assertIsNone(parse_seed_id(""))

    def test_is_english(self):
        self.assertTrue(is_english("Please summarise this article about rivers."))
        self.assertFalse(is_english("Ich bin nicht sicher, ob das die richtige Antwort ist und"))
        self.assertFalse(is_english("Привет, как дела у тебя сегодня"))

    def test_system_prompt_key(self):
        self.assertEqual(system_prompt_key("  You are   A bot"), "you are a bot")

    def test_paraphrase_valid(self):
        terms = ["jailbreak", "prompt"]
        src = "Explain what a jailbreak prompt is to my students."
        self.assertTrue(
            paraphrase_valid(src, "Describe to my class what a jailbreak prompt means.", terms)
        )
        self.assertFalse(
            paraphrase_valid(src, "Describe to my class what such an attack means.", terms)
        )
        self.assertFalse(
            paraphrase_valid(src, "I'm sorry, but I can't help with that request.", terms)
        )
        self.assertFalse(paraphrase_valid(src, "short", terms))

    def test_framing_cells_and_lengths(self):
        lengths = [len(p) for cell in FRAMING_CELLS.values() for p in cell]
        mean = np.mean(lengths)
        self.assertTrue(all(0.85 * mean <= n <= 1.15 * mean for n in lengths))
        self.assertTrue(all(len(c) == 24 and len(set(c)) == 24 for c in FRAMING_CELLS.values()))
        out = framed(["a b c", "d e f"], 1)
        self.assertEqual(sorted(out), sorted(FRAMING_CELLS))
        for cell, (texts, idx) in out.items():
            for t, i in zip(texts, idx):
                self.assertTrue(t.startswith(FRAMING_CELLS[cell][i]))
        self.assertEqual(framed(["a b c"], 1), framed(["a b c"], 1))


class InferenceTests(unittest.TestCase):
    def test_unpaired_bootstrap_recovers_difference(self):
        rng = np.random.default_rng(0)
        a = (rng.random((8, 400)) < 0.30).astype(float)
        b = (rng.random((5, 400)) < 0.10).astype(float)
        reps = unpaired_bootstrap_diff(a, b, np.arange(400), 1000, np.random.default_rng(1))
        lo, hi = percentile(reps, 0.95)
        self.assertLess(lo, 0.2)
        self.assertGreater(hi, 0.2)
        self.assertLess(boot_p_two_sided(reps), 0.01)

    def test_identical_arms_center_on_zero(self):
        f = (np.random.default_rng(2).random((6, 300)) < 0.2).astype(float)
        reps = unpaired_bootstrap_diff(f, f, np.arange(300), 2000, np.random.default_rng(3))
        self.assertLess(abs(np.median(reps)), 0.01)

    def test_paired_within_model(self):
        raw = np.ones((4, 50))
        para = np.zeros((4, 50))
        reps = paired_within_model_diff(raw, para, np.arange(50), 200, np.random.default_rng(4))
        self.assertTrue(np.allclose(reps, 1.0))

    def test_interaction(self):
        mask = np.r_[np.ones(100, bool), np.zeros(100, bool)]
        a = np.zeros((3, 200))
        a[:, :100] = 1  # arm a: 1 on stratum 1, 0 on stratum 2
        b = np.zeros((4, 200))
        reps = unpaired_bootstrap_interaction(
            a, b, np.arange(200), mask, ~mask, 200, np.random.default_rng(5)
        )
        self.assertTrue(np.allclose(reps, 1.0))

    def test_twoway_cell_diff(self):
        fa = np.ones((3, 60))
        fb = np.zeros((3, 60))
        pa = np.arange(60) % 24
        reps = twoway_cell_diff(fa, fb, pa, pa, np.arange(60), 200, np.random.default_rng(6))
        self.assertTrue(np.allclose(reps, 1.0))

    def test_noninferiority_p(self):
        self.assertEqual(boot_p_noninferior(np.full(100, 0.0), 0.02), 0.0)
        self.assertEqual(boot_p_noninferior(np.full(100, -0.05), 0.02), 1.0)

    def test_holm(self):
        rejected, used = holm([0.001, 0.04, 0.03, 0.2])
        self.assertEqual(rejected, [True, False, False, False])
        self.assertAlmostEqual(used[0], 0.0125)
        rejected, _ = holm([0.001, 0.012, 0.02])
        self.assertEqual(rejected, [True, True, True])

    def test_welch(self):
        lo, hi = welch_interval([0.3, 0.32, 0.28, 0.31], [0.1, 0.12, 0.09], 0.95)
        self.assertLess(lo, 0.2)
        self.assertGreater(hi, 0.18)
        self.assertGreater(lo, 0.1)


if __name__ == "__main__":
    unittest.main()
