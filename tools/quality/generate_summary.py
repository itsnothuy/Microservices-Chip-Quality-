#!/usr/bin/env python3
"""
Generate validation summary from individual validation reports.
Used by the GitHub Actions workflow.
"""

import json
import glob
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def collect_validation_reports() -> List[Dict[str, Any]]:
    """Collect all validation reports from the current directory."""
    reports = []
    total_errors = 0
    total_warnings = 0
    
    for report_file in glob.glob('validation-report-*.json'):
        try:
            with open(report_file) as f:
                data = json.load(f)
                reports.append(data)
                print(f"✅ Loaded report: {report_file}")
        except Exception as e:
            print(f"❌ Error reading {report_file}: {e}")
    
    return reports


def calculate_summary_metrics(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary metrics from validation reports."""
    if not reports:
        return {
            'validation_time': datetime.now().isoformat(),
            'total_issues_validated': 0,
            'overall_quality_score': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'all_validations_passed': False,
            'reports': []
        }
    
    total_errors = 0
    total_warnings = 0
    total_quality_score = 0
    
    for report in reports:
        validation_summary = report.get('validation_summary', {})
        total_errors += validation_summary.get('total_errors', 0)
        total_warnings += validation_summary.get('total_warnings', 0)
        total_quality_score += report.get('quality_score', 0)
    
    avg_quality_score = total_quality_score / len(reports) if reports else 0
    
    return {
        'validation_time': datetime.now().isoformat(),
        'total_issues_validated': len(reports),
        'overall_quality_score': round(avg_quality_score, 2),
        'total_errors': total_errors,
        'total_warnings': total_warnings,
        'all_validations_passed': total_errors == 0,
        'quality_threshold_met': avg_quality_score >= 80,
        'reports': reports
    }


def main():
    """Main function to generate validation summary."""
    parser = argparse.ArgumentParser(description='Generate validation summary')
    parser.add_argument('--output', '-o', default='validation-summary.json',
                       help='Output file for validation summary')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    print("📊 Generating validation summary...")
    
    # Collect all validation reports
    reports = collect_validation_reports()
    
    if args.verbose:
        print(f"Found {len(reports)} validation reports")
    
    # Calculate summary metrics
    summary = calculate_summary_metrics(reports)
    
    # Write summary to file
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary for CI logs
    print(f"✅ Validation summary saved to {output_path}")
    print(f"📊 Overall quality score: {summary['overall_quality_score']}/100")
    print(f"🔍 Total issues validated: {summary['total_issues_validated']}")
    print(f"❌ Total errors: {summary['total_errors']}")
    print(f"⚠️  Total warnings: {summary['total_warnings']}")
    print(f"✅ All validations passed: {summary['all_validations_passed']}")
    print(f"🎯 Quality threshold met: {summary['quality_threshold_met']}")
    
    # Exit with error code if validations failed
    if not summary['all_validations_passed']:
        print("❌ Validation failed - exiting with error code 1")
        exit(1)
    
    print("🎉 All validations passed!")


if __name__ == '__main__':
    main()