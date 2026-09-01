#!/usr/bin/env python3
"""
ChemMind DevOps Test Verification Suite
Runs the AI subsystem tests plus the repository contract suite (frontend
contracts and cross-module checks) and prints a structured readiness report.

Usage:
    python3 scripts/verify_devops_tests.py
"""

import os
import sys
import time


def run_devops_verification():
    import pytest

    print("=" * 70)
    print("      CHEMMIND AI RAG FOUNDATION — DEVOPS TEST VERIFICATION HARNESS")
    print("=" * 70)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, project_root)

    test_targets = [
        os.path.join(project_root, "ai", "tests"),
        os.path.join(project_root, "tests"),
    ]

    print(f"[*] Discovering test modules in: {', '.join(test_targets)}")

    start_time = time.time()
    exit_code = pytest.main(
        test_targets + ["-q", "-p", "no:cacheprovider", "--tb=short"]
    )
    elapsed_time = round(time.time() - start_time, 3)

    print("\n" + "=" * 70)
    print("                     DEVOPS VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"  Execution Duration   : {elapsed_time}s")
    print(f"  Suite Exit Code      : {exit_code}")

    if exit_code == 0:
        print("\n[SUCCESS] ALL CHEMMIND AI & CONTRACT MODULES ARE OPERATIONAL & PASSED VERIFICATION.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n[FAILURE] DEVOPS VERIFICATION FAILED. CHECK LOGS ABOVE.")
        print("=" * 70)
        sys.exit(exit_code)


if __name__ == "__main__":
    run_devops_verification()