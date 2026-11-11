"""test_report_data.py - the Demo 3 numbers that docs/report_data.md publishes."""
import unittest

from python_sim.report_data import core1_breakdown, demo3_summary, run_demo


class TestReportData(unittest.TestCase):
    def test_demo3_core1_breakdown(self):
        """Core 1 (25 cycles): 15 instructions summing 9..16, then the flag loop
        LOAD/BEQ at cycles 15-20 (flag read 0 at 15 and 17, 1 at 19; BEQ falls
        through at 20) = 6, then LOAD/ADD/STORE/HALT = 4.  15 + 6 + 4 = 25."""
        self.assertEqual(core1_breakdown(run_demo("demo3")), (15, 6, 4))

    def test_demo3_speedup_and_serial_fraction(self):
        """S = 33/25 = 1.32;  f = 2/S - 1 = 50/33 - 1 = 17/33 = 51.5%."""
        text = demo3_summary(run_demo("demo3"), run_demo("single"))
        self.assertIn("max(19, 25) = 25", text)
        self.assertIn("33/25 = 1.32", text)
        self.assertIn("17/33 = 51.5%", text)


if __name__ == "__main__":
    unittest.main()
