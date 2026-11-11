"""test_run.py - the CLI (no testbench counterpart)."""
import contextlib
import glob
import io
import os
import unittest

from python_sim.instr_mem import InstructionMemory
from python_sim.run import load_program, main
from python_sim.tests import REPO, prog


class TestRun(unittest.TestCase):
    def test_asm_loads_same_as_hex(self):
        """Every programs/*.asm assembled in memory equals its checked-in .hex."""
        for asm in glob.glob(os.path.join(REPO, "programs", "*.asm")):
            with self.subTest(os.path.basename(asm)):
                self.assertEqual(load_program(asm).mem, InstructionMemory(asm[:-4] + ".hex").mem)

    def test_cli_demo1_output(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = main(["--prog0", prog("demo1_core0.hex"), "--prog1", prog("demo1_core1.hex"),
                       "--data", prog("data1.hex"), "--trace"])
        text = out.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("cycle    4  core0  pc   4  F000  HALT", text)
        self.assertIn("[40]=11  [41]=0C", text)
        self.assertIn("dual-core time = max(C0, C1) = 8", text)


if __name__ == "__main__":
    unittest.main()
