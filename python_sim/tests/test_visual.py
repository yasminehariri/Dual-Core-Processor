"""Tests for python_sim/visual.py (skipped when matplotlib is not installed)."""
import os
import tempfile
import unittest

from python_sim import visual

REPO = visual.REPO


def prog(name):
    return os.path.join(REPO, "programs", name)


class TestRecord(unittest.TestCase):
    def test_demo2_frames_match_the_simulator(self):
        fr = visual.record(prog("demo2_core0.asm"), prog("demo2_core1.asm"), prog("data2.hex"))
        self.assertEqual(len(fr) - 1, 13, "one frame per clock cycle plus the start frame")
        self.assertEqual(fr[-1].counts, (7, 13))
        self.assertEqual(fr[-1].mem[0x81], 0x28)
        self.assertEqual(fr[6].mem_written, {0xF0: 0}, "Core 0 raises the flag in cycle 5")

    def test_conflict_marks_core0_as_writer(self):
        fr = visual.record(prog("conflict_core0.asm"), prog("conflict_core1.asm"), None)
        self.assertEqual(fr[2].mem_written, {0x50: 0})
        self.assertEqual(fr[-1].mem[0x50], 0xAA)


@unittest.skipUnless(__import__("importlib").util.find_spec("matplotlib"), "matplotlib not installed")
class TestPictures(unittest.TestCase):
    def test_save_viewer_and_waves(self):
        with tempfile.TemporaryDirectory() as d:
            for args in (["--demo", "1", "--frame", "5"], ["--demo", "3", "--waves"]):
                out = os.path.join(d, "x.png")
                self.assertEqual(visual.main(args + ["--save", out]), 0)
                self.assertGreater(os.path.getsize(out), 10000)


if __name__ == "__main__":
    unittest.main()
