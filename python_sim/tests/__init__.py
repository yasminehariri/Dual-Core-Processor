"""Tests for python_sim. One file per Verilog testbench in tb/ (test_alu.py <-> tb_alu.v, ...)."""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def prog(name: str) -> str:
    """Absolute path of a file in programs/."""
    return os.path.join(REPO, "programs", name)
