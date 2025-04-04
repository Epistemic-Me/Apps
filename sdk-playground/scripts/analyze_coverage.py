#!/usr/bin/env python3
"""
Script to analyze test coverage and generate reports.
Also identifies which tests need to be run based on changed files.
"""

import os
import sys
import json
import re
from typing import List, Dict, Set
import subprocess
import argparse

def parse_test_index() -> Dict[str, Set[str]]:
    """Parse TEST_INDEX.md to get file to test mappings"""
    dependencies = {}
    try:
        with open("docs/TEST_INDEX.md", "r") as f:
            content = f.read()
            
        # Extract table rows using regex
        pattern = r"\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*[^|]+\|"
        matches = re.finditer(pattern, content)
        
        for match in matches:
            source_file = match.group(1)
            test_files = re.findall(r"`([^`]+)`", match.group(2))
            dependencies[source_file] = set(test_files)
            
        # Extract additional dependencies from sections
        sections = {
            "UI Changes": r"### UI Changes\n(.*?)(?=###|\Z)",
            "Service Changes": r"### Service Changes\n(.*?)(?=###|\Z)",
            "Model Changes": r"### Model Changes\n(.*?)(?=###|\Z)",
            "Data Generation Changes": r"### Data Generation Changes\n(.*?)(?=###|\Z)"
        }
        
        for section, pattern in sections.items():
            match = re.search(pattern, content, re.DOTALL)
            if match:
                section_content = match.group(1)
                # Extract test paths
                test_paths = re.findall(r"`([^`]+)`", section_content)
                # Add to dependencies based on file type
                for source_file in dependencies:
                    if section.lower().split()[0] in source_file:
                        dependencies[source_file].update(
                            path for path in test_paths if path.endswith(".py")
                        )
        
        return dependencies
    except FileNotFoundError:
        print("Warning: TEST_INDEX.md not found. Using default mappings.")
        return get_default_test_dependencies()

def get_default_test_dependencies() -> Dict[str, Set[str]]:
    """Fallback test dependencies if TEST_INDEX.md is not available"""
    return {
        "src/ui/app.py": {
            "tests/ui/test_app.py",
            "tests/integration/test_app_integration.py"
        },
        "src/services/evaluation.py": {
            "tests/services/test_evaluation.py",
            "tests/integration/test_evaluation_integration.py"
        }
    }

def run_coverage() -> str:
    """Run pytest with coverage and return the coverage report"""
    result = subprocess.run(
        ["pytest", "--cov=src", "--cov-report=json", "tests/"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Error running tests:")
        print(result.stderr)
        sys.exit(1)
    
    return result.stdout

def load_coverage_data() -> Dict:
    """Load coverage data from .coverage-json file"""
    try:
        with open("coverage.json") as f:
            return json.load(f)
    except FileNotFoundError:
        print("No coverage data found. Run tests first.")
        sys.exit(1)

def get_tests_to_run(changed_files: List[str]) -> Set[str]:
    """Return set of tests that need to be run based on changed files"""
    dependencies = parse_test_index()
    tests_to_run = set()
    
    for file in changed_files:
        if file in dependencies:
            tests_to_run.update(dependencies[file])
            
            # If a model or service changes, run integration tests
            if "models/" in file or "services/" in file:
                tests_to_run.add("tests/integration/")
    
    return tests_to_run

def analyze_coverage(coverage_data: Dict) -> Dict:
    """Analyze coverage data and return summary"""
    summary = {
        "total": coverage_data["totals"]["percent_covered"],
        "files": {}
    }
    
    for file, data in coverage_data["files"].items():
        if file.startswith("src/"):
            summary["files"][file] = {
                "coverage": data["summary"]["percent_covered"],
                "missing_lines": data["missing_lines"],
                "excluded_lines": data["excluded_lines"]
            }
    
    return summary

def print_coverage_report(summary: Dict):
    """Print formatted coverage report"""
    print("\nCoverage Report")
    print("=" * 80)
    print(f"Total Coverage: {summary['total']:.2f}%\n")
    
    print("File Coverage:")
    print("-" * 80)
    for file, data in summary["files"].items():
        print(f"{file}:")
        print(f"  Coverage: {data['coverage']:.2f}%")
        if data["missing_lines"]:
            print(f"  Missing Lines: {data['missing_lines']}")
        print()

def check_coverage_requirements(summary: Dict):
    """Check if coverage meets requirements"""
    requirements = {
        "unit": 90.0,
        "integration": 80.0,
        "ui": 70.0
    }
    
    print("\nCoverage Requirements Check:")
    print("-" * 80)
    
    # Check UI components
    ui_files = [f for f in summary["files"] if "/ui/" in f]
    if ui_files:
        ui_coverage = sum(summary["files"][f]["coverage"] for f in ui_files) / len(ui_files)
        print(f"UI Coverage: {ui_coverage:.2f}% (Required: {requirements['ui']}%)")
        if ui_coverage < requirements['ui']:
            print("  ❌ UI coverage below requirement")
    
    # Check unit tests (models and services)
    unit_files = [f for f in summary["files"] if "/models/" in f or "/services/" in f]
    if unit_files:
        unit_coverage = sum(summary["files"][f]["coverage"] for f in unit_files) / len(unit_files)
        print(f"Unit Test Coverage: {unit_coverage:.2f}% (Required: {requirements['unit']}%)")
        if unit_coverage < requirements['unit']:
            print("  ❌ Unit test coverage below requirement")

def main():
    parser = argparse.ArgumentParser(description="Analyze test coverage and dependencies")
    parser.add_argument("--changed-files", nargs="*", help="List of changed files")
    args = parser.parse_args()
    
    # Run coverage if no report exists
    if not os.path.exists("coverage.json"):
        print("Running tests to generate coverage data...")
        run_coverage()
    
    # Load and analyze coverage data
    coverage_data = load_coverage_data()
    summary = analyze_coverage(coverage_data)
    print_coverage_report(summary)
    check_coverage_requirements(summary)
    
    # If changed files provided, show which tests to run
    if args.changed_files:
        tests = get_tests_to_run(args.changed_files)
        if tests:
            print("\nTests to run:")
            print("-" * 80)
            for test in sorted(tests):
                print(f"pytest {test} -v")
        else:
            print("\nNo specific tests found for the changed files")

if __name__ == "__main__":
    main() 