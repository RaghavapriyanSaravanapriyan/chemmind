#!/usr/bin/env python3
"""
ChemMind DevOps Test Verification Suite
Run this standalone script to execute all ChemMind AI tests and verify system readiness.

Usage:
    python3 scripts/verify_devops_tests.py
"""

import os
import sys
import time
import unittest

def run_devops_verification():
    print("=" * 70)
    print("      CHEMMIND AI RAG FOUNDATION — DEVOPS TEST VERIFICATION HARNESS")
    print("=" * 70)

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, project_root)

    test_dir = os.path.join(project_root, "ai", "tests")
    print(f"[*] Discovering test modules in: {test_dir}")

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern="test_*.py")

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    elapsed_time = round(time.time() - start_time, 3)

    print("\n" + "=" * 70)
    print("                     DEVOPS VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"  Total Tests Executed : {result.testsRun}")
    print(f"  Successful Passes    : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures             : {len(result.failures)}")
    print(f"  Errors               : {len(result.errors)}")
    print(f"  Execution Duration   : {elapsed_time}s")

    if result.wasSuccessful():
        print("\n[SUCCESS] ALL CHEMMIND AI MODULES ARE OPERATIONAL & PASSED VERIFICATION.")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n[FAILURE] DEVOPS VERIFICATION FAILED. CHECK LOGS ABOVE.")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    run_devops_verification()
