#!/usr/bin/env python3
"""
ChemMind DevOps Master Test Suite Runner
Executes the comprehensive automated test suite and prints structured verification results.

Usage:
    python devops/tests/run_all_tests.py
"""

import os
import sys
import time
from pathlib import Path
import pytest

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

# Ensure proper paths in sys.path
for p in [str(REPO_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def main():
    print("=" * 80)
    print("      CHEMMIND AI RAG PLATFORM — DEVOPS AUTOMATED TEST SUITE RUNNER")
    print("=" * 80)
    print(f"[*] Discovery Directory : {TEST_DIR}")
    print(f"[*] Root Directory      : {REPO_ROOT}")
    print("=" * 80 + "\n")

    start_time = time.time()

    pytest_args = [
        str(TEST_DIR),
        "-v",
        "--tb=short",
        "-p", "no:warnings",
    ]

    exit_code = pytest.main(pytest_args)
    elapsed = round(time.time() - start_time, 2)

    print("\n" + "=" * 80)
    print("                       DEVOPS TEST EXECUTION REPORT")
    print("=" * 80)
    print(f"[*] Execution Duration : {elapsed}s")
    if exit_code == 0:
        print("[*] Suite Status       : [SUCCESS] ALL 13 TEST CATEGORIES PASSED")
    else:
        print(f"[*] Suite Status       : [FAILURE] Exit code {exit_code}")
    print("=" * 80)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
