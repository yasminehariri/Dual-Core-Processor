"""test_shared_mem.py - mirrors tb/tb_shared_mem.v (11 checks)."""
import unittest

from python_sim.shared_mem import SharedMemory
from python_sim.tests import prog


class TestSharedMem(unittest.TestCase):
    def test_tb_shared_mem(self):
        m = SharedMemory(prog("data1.hex"))
        self.assertEqual(m.read(0x00), 0x0C, "init: data1.hex byte 0")
        self.assertEqual(m.read(0x02), 0x03, "init: data1.hex byte 2")
        self.assertEqual(m.read(0x77), 0x00, "untouched byte reads 00")
        self.assertEqual(m.read(0xFF), 0x00, "last byte reads 00")

        # port 0 writes 0x40; port 1 reads it during the cycle (old) and after the edge (new)
        self.assertEqual(m.read(0x40), 0x00, "read during write sees old value")
        m.clock(0x40, 0x11, 1, 0x40, 0, 0)
        self.assertEqual(m.read(0x40), 0x11, "port 1 sees port 0's write next cycle")

        m.clock(0x41, 0, 0, 0x41, 0x22, 1)
        self.assertEqual(m.read(0x41), 0x22, "port 0 sees port 1's write")

        m.clock(0x60, 0xA0, 1, 0x61, 0xB1, 1)
        self.assertEqual(m.read(0x60), 0xA0, "simultaneous write, port 0 address")
        self.assertEqual(m.read(0x61), 0xB1, "simultaneous write, port 1 address")

        m.clock(0x50, 0xAA, 1, 0x50, 0x55, 1)
        self.assertEqual(m.read(0x50), 0xAA, "conflict: Core 0 wins")


if __name__ == "__main__":
    unittest.main()
