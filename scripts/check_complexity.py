#!/usr/bin/env python3
"""
Cyclomatic complexity guard.
Fails (exit 1) if any function/method has CC grade C or above (score > 10).

CC scale:  A 1-5  B 6-10  C 11-15 (FAIL)  D 16-20  E 21-25  F >25
"""
import subprocess, sys, os, re

ROOT = os.path.join(os.path.dirname(__file__), "..")
API_PATH = os.path.join(ROOT, "apps", "api", "app")


def main():
    print("=== Cyclomatic Complexity Check (radon) ===")

    # -n C → only print functions with grade C or above (CC > 10)
    result = subprocess.run(
        ["radon", "cc", API_PATH, "-s", "-n", "C"],
        capture_output=True, text=True,
    )
    # Average run (separate call, just for display)
    avg_result = subprocess.run(
        ["radon", "cc", API_PATH, "--total-average"],
        capture_output=True, text=True,
    )
    avg_line = next(
        (l for l in avg_result.stdout.splitlines() if "Average complexity" in l), ""
    )
    if avg_line:
        print(avg_line)

    violations = [
        line for line in result.stdout.splitlines()
        if line.strip() and re.search(r"\b[CDEF]\b", line)
    ]

    if violations:
        print("\nFAIL — Functions with CC > 10:")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)

    print("PASS — All functions have CC <= 10")
    sys.exit(0)


if __name__ == "__main__":
    main()
