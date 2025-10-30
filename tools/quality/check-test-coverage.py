#!/usr/bin/env python3
"""
Test coverage validation script.
Ensures minimum test coverage requirements are met.
"""

import subprocess
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any


def run_coverage_check(min_coverage: float = 80.0) -> Dict[str, Any]:
    """Run pytest with coverage and return results."""
    try:
        # Run tests with coverage
        result = subprocess.run([
            sys.executable, '-m', 'pytest',
            '--cov=services',
            '--cov=tests', 
            '--cov-report=json',
            '--cov-report=term-missing',
            '--cov-fail-under=' + str(min_coverage),
            'tests/'
        ], capture_output=True, text=True, cwd=Path.cwd())
        
        # Read coverage report
        coverage_data = {}
        if Path('coverage.json').exists():
            with open('coverage.json') as f:
                coverage_data = json.load(f)
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'coverage_data': coverage_data,
            'overall_coverage': coverage_data.get('totals', {}).get('percent_covered', 0)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'overall_coverage': 0
        }


def check_critical_modules_coverage(coverage_data: Dict[str, Any], min_coverage: float = 90.0) -> Dict[str, Any]:
    """Check coverage for critical modules."""
    critical_modules = [
        'services/shared/models',
        'services/shared/database',
        'services/shared/enums'
    ]
    
    results = {}
    files = coverage_data.get('files', {})
    
    for module in critical_modules:
        module_files = [f for f in files.keys() if f.startswith(module)]
        if not module_files:
            results[module] = {'coverage': 0, 'status': 'missing'}
            continue
            
        # Calculate average coverage for module
        total_statements = 0
        covered_statements = 0
        
        for file_path in module_files:
            file_data = files[file_path]['summary']
            total_statements += file_data['num_statements']
            covered_statements += file_data['covered_lines']
        
        if total_statements > 0:
            coverage = (covered_statements / total_statements) * 100
            status = 'pass' if coverage >= min_coverage else 'fail'
        else:
            coverage = 0
            status = 'empty'
        
        results[module] = {
            'coverage': round(coverage, 2),
            'status': status,
            'files': len(module_files)
        }
    
    return results


def main():
    """Main function for test coverage validation."""
    parser = argparse.ArgumentParser(description='Validate test coverage')
    parser.add_argument('--min-coverage', type=float, default=80.0,
                       help='Minimum overall coverage percentage')
    parser.add_argument('--min-critical-coverage', type=float, default=90.0,
                       help='Minimum coverage for critical modules')
    parser.add_argument('--fail-fast', action='store_true',
                       help='Exit immediately on first failure')
    
    args = parser.parse_args()
    
    print("🧪 Running test coverage validation...")
    
    # Run coverage check
    coverage_result = run_coverage_check(args.min_coverage)
    
    if not coverage_result['success']:
        print("❌ Test coverage check failed")
        if 'error' in coverage_result:
            print(f"Error: {coverage_result['error']}")
        else:
            print(f"stdout: {coverage_result['stdout']}")
            print(f"stderr: {coverage_result['stderr']}")
        
        if args.fail_fast:
            sys.exit(1)
    
    overall_coverage = coverage_result.get('overall_coverage', 0)
    print(f"📊 Overall test coverage: {overall_coverage:.1f}%")
    
    # Check critical modules if we have coverage data
    if 'coverage_data' in coverage_result and coverage_result['coverage_data']:
        print("🔍 Checking critical module coverage...")
        critical_results = check_critical_modules_coverage(
            coverage_result['coverage_data'], 
            args.min_critical_coverage
        )
        
        all_critical_passed = True
        for module, result in critical_results.items():
            status_emoji = "✅" if result['status'] == 'pass' else "❌"
            print(f"{status_emoji} {module}: {result['coverage']:.1f}% ({result['files']} files)")
            
            if result['status'] != 'pass':
                all_critical_passed = False
        
        if not all_critical_passed:
            print("❌ Critical module coverage requirements not met")
            if args.fail_fast:
                sys.exit(1)
    
    # Final validation
    if overall_coverage >= args.min_coverage:
        print(f"✅ Test coverage validation passed ({overall_coverage:.1f}% >= {args.min_coverage}%)")
        sys.exit(0)
    else:
        print(f"❌ Test coverage validation failed ({overall_coverage:.1f}% < {args.min_coverage}%)")
        sys.exit(1)


if __name__ == '__main__':
    main()