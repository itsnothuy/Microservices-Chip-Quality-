#!/usr/bin/env python3
# ================================================================================================
# 🚀 TEST RUNNER - COMPREHENSIVE TEST EXECUTION ORCHESTRATOR
# ================================================================================================
# Production-grade test runner for semiconductor manufacturing platform
# Features: Parallel execution, coverage reporting, CI/CD integration, performance monitoring
# Supports: Unit, Integration, E2E, Performance, Security, Compliance testing
# ================================================================================================

import os
import sys
import argparse
import asyncio
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import tempfile

import pytest
import psutil

# ================================================================================================
# 📊 TEST EXECUTION CONFIGURATION
# ================================================================================================

@dataclass
class TestConfig:
    """Configuration for test execution."""
    test_types: List[str]
    parallel_workers: int
    coverage_threshold: float
    timeout_seconds: int
    environment: str
    report_formats: List[str]
    failure_threshold: float
    verbose: bool
    fast_fail: bool
    cleanup_after: bool

@dataclass 
class TestResults:
    """Results from test execution."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    duration_seconds: float
    coverage_percentage: float
    test_files: List[str]
    failed_test_details: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    exit_code: int

# ================================================================================================
# 🎯 TEST SUITE DEFINITIONS
# ================================================================================================

TEST_SUITES = {
    "unit": {
        "path": "tests/unit/",
        "markers": "unit",
        "timeout": 300,  # 5 minutes
        "parallel": True,
        "coverage_required": True,
        "description": "Fast isolated unit tests"
    },
    "integration": {
        "path": "tests/integration/", 
        "markers": "integration",
        "timeout": 900,  # 15 minutes
        "parallel": True,
        "coverage_required": True,
        "description": "Multi-service integration tests"
    },
    "e2e": {
        "path": "tests/e2e/",
        "markers": "e2e",
        "timeout": 1800,  # 30 minutes
        "parallel": False,
        "coverage_required": False,
        "description": "End-to-end workflow tests"
    },
    "performance": {
        "path": "tests/performance/",
        "markers": "performance",
        "timeout": 2400,  # 40 minutes
        "parallel": False,
        "coverage_required": False,
        "description": "Performance and load tests"
    },
    "security": {
        "path": "tests/security/",
        "markers": "security",
        "timeout": 1200,  # 20 minutes
        "parallel": True,
        "coverage_required": False,
        "description": "Security vulnerability tests"
    },
    "compliance": {
        "path": "tests/compliance/",
        "markers": "compliance",
        "timeout": 600,  # 10 minutes
        "parallel": True,
        "coverage_required": False,
        "description": "Regulatory compliance tests"
    }
}

# ================================================================================================
# 🧪 TEST RUNNER CLASS
# ================================================================================================

class TestRunner:
    """Main test runner orchestrator."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.start_time = time.time()
        self.results = TestResults(
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            duration_seconds=0.0,
            coverage_percentage=0.0,
            test_files=[],
            failed_test_details=[],
            performance_metrics={},
            exit_code=0
        )
        
        # Create output directories
        self.output_dir = Path("test-results")
        self.output_dir.mkdir(exist_ok=True)
        
        self.reports_dir = self.output_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        self.coverage_dir = self.output_dir / "coverage"
        self.coverage_dir.mkdir(exist_ok=True)
    
    async def run_all_tests(self) -> TestResults:
        """Run all configured test suites."""
        
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        print(f"Environment: {self.config.environment}")
        print(f"Test Types: {', '.join(self.config.test_types)}")
        print(f"Parallel Workers: {self.config.parallel_workers}")
        print(f"Coverage Threshold: {self.config.coverage_threshold:.1%}")
        print("=" * 60)
        
        # Pre-test setup
        await self._setup_test_environment()
        
        # Run test suites in order
        suite_results = []
        
        for test_type in self.config.test_types:
            if test_type not in TEST_SUITES:
                print(f"⚠️ Unknown test type: {test_type}")
                continue
            
            print(f"\n📊 Running {test_type.upper()} Tests")
            print("-" * 40)
            
            suite_config = TEST_SUITES[test_type]
            suite_result = await self._run_test_suite(test_type, suite_config)
            suite_results.append(suite_result)
            
            # Check for early exit on failure
            if self.config.fast_fail and suite_result["failed"] > 0:
                print(f"❌ Fast fail enabled, stopping after {test_type} failures")
                break
        
        # Aggregate results
        await self._aggregate_results(suite_results)
        
        # Generate reports
        await self._generate_reports()
        
        # Cleanup
        if self.config.cleanup_after:
            await self._cleanup_test_environment()
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    async def _setup_test_environment(self):
        """Setup test environment and dependencies."""
        
        print("🔧 Setting up test environment...")
        
        # Check if Docker services are running (for integration tests)
        if any(test_type in ["integration", "e2e"] for test_type in self.config.test_types):
            if not await self._check_docker_services():
                print("⚠️ Docker services not running, some tests may fail")
        
        # Set environment variables
        test_env = {
            "ENVIRONMENT": "test",
            "LOG_LEVEL": "DEBUG" if self.config.verbose else "INFO",
            "PYTHONPATH": str(Path.cwd()),
            "COVERAGE_PROCESS_START": str(Path.cwd() / ".coveragerc")
        }
        
        for key, value in test_env.items():
            os.environ[key] = value
        
        # Create test data directories
        test_data_dir = Path("test-data")
        test_data_dir.mkdir(exist_ok=True)
        
        print("✅ Test environment setup complete")
    
    async def _check_docker_services(self) -> bool:
        """Check if required Docker services are running."""
        
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            running_services = result.stdout.strip().split('\n')
            required_services = [
                "postgres", "redis", "kafka", "minio"
            ]
            
            missing_services = []
            for service in required_services:
                if not any(service in container for container in running_services):
                    missing_services.append(service)
            
            if missing_services:
                print(f"⚠️ Missing Docker services: {', '.join(missing_services)}")
                return False
            
            return True
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def _run_test_suite(self, test_type: str, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test suite."""
        
        start_time = time.time()
        
        # Build pytest command
        cmd = self._build_pytest_command(test_type, suite_config)
        
        print(f"Command: {' '.join(cmd)}")
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite_config["timeout"]
            )
            
            duration = time.time() - start_time
            
            # Parse pytest output
            suite_result = self._parse_pytest_output(result, test_type, duration)
            
            print(f"✅ {test_type.upper()} tests completed in {duration:.1f}s")
            print(f"   Passed: {suite_result['passed']}, Failed: {suite_result['failed']}, Skipped: {suite_result['skipped']}")
            
            return suite_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"⏰ {test_type.upper()} tests timed out after {duration:.1f}s")
            
            return {
                "test_type": test_type,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "duration": duration,
                "exit_code": 124,  # Timeout exit code
                "output": "Tests timed out",
                "error": f"Tests exceeded {suite_config['timeout']} second timeout"
            }
        
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {test_type.upper()} tests failed with error: {e}")
            
            return {
                "test_type": test_type,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "duration": duration,
                "exit_code": 1,
                "output": "",
                "error": str(e)
            }
    
    def _build_pytest_command(self, test_type: str, suite_config: Dict[str, Any]) -> List[str]:
        """Build pytest command for test suite."""
        
        cmd = ["python", "-m", "pytest"]
        
        # Test path
        cmd.append(suite_config["path"])
        
        # Markers
        if suite_config["markers"]:
            cmd.extend(["-m", suite_config["markers"]])
        
        # Parallel execution
        if suite_config["parallel"] and self.config.parallel_workers > 1:
            cmd.extend(["-n", str(self.config.parallel_workers)])
        
        # Verbosity
        if self.config.verbose:
            cmd.append("-v")
        
        # Fast fail
        if self.config.fast_fail:
            cmd.append("-x")
        
        # Coverage
        if suite_config["coverage_required"]:
            cmd.extend([
                "--cov=services",
                "--cov-report=xml",
                f"--cov-report=html:{self.coverage_dir}/{test_type}",
                "--cov-append"
            ])
        
        # Output formats
        report_file = self.reports_dir / f"{test_type}_results.xml"
        cmd.extend(["--junitxml", str(report_file)])
        
        if "html" in self.config.report_formats:
            html_file = self.reports_dir / f"{test_type}_report.html"
            cmd.extend(["--html", str(html_file), "--self-contained-html"])
        
        if "json" in self.config.report_formats:
            json_file = self.reports_dir / f"{test_type}_results.json"
            cmd.extend(["--json-report", "--json-report-file", str(json_file)])
        
        # Timeout for individual tests
        cmd.extend(["--timeout", "300"])  # 5 minute timeout per test
        
        return cmd
    
    def _parse_pytest_output(self, result: subprocess.CompletedProcess, test_type: str, duration: float) -> Dict[str, Any]:
        """Parse pytest output to extract results."""
        
        output_lines = result.stdout.split('\n')
        
        # Default values
        passed = 0
        failed = 0
        skipped = 0
        
        # Parse summary line
        for line in output_lines:
            if "passed" in line and ("failed" in line or "error" in line or "skipped" in line):
                # Example: "10 passed, 2 failed, 1 skipped in 5.23s"
                import re
                
                passed_match = re.search(r'(\d+) passed', line)
                if passed_match:
                    passed = int(passed_match.group(1))
                
                failed_match = re.search(r'(\d+) (?:failed|error)', line)
                if failed_match:
                    failed = int(failed_match.group(1))
                
                skipped_match = re.search(r'(\d+) skipped', line)
                if skipped_match:
                    skipped = int(skipped_match.group(1))
                
                break
        
        return {
            "test_type": test_type,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
    
    async def _aggregate_results(self, suite_results: List[Dict[str, Any]]):
        """Aggregate results from all test suites."""
        
        for suite_result in suite_results:
            self.results.total_tests += suite_result["passed"] + suite_result["failed"] + suite_result["skipped"]
            self.results.passed_tests += suite_result["passed"]
            self.results.failed_tests += suite_result["failed"]
            self.results.skipped_tests += suite_result["skipped"]
            
            if suite_result["failed"] > 0:
                self.results.failed_test_details.append({
                    "test_type": suite_result["test_type"],
                    "failed_count": suite_result["failed"],
                    "error": suite_result.get("error", ""),
                    "output": suite_result.get("output", "")
                })
        
        self.results.duration_seconds = time.time() - self.start_time
        
        # Calculate overall exit code
        if self.results.failed_tests > 0:
            failure_rate = self.results.failed_tests / self.results.total_tests
            if failure_rate > self.config.failure_threshold:
                self.results.exit_code = 1
        
        # Get coverage if available
        coverage_file = Path("coverage.xml")
        if coverage_file.exists():
            self.results.coverage_percentage = await self._parse_coverage_report(coverage_file)
    
    async def _parse_coverage_report(self, coverage_file: Path) -> float:
        """Parse coverage report to extract percentage."""
        
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            # Find coverage element
            coverage_elem = root.find('.//coverage')
            if coverage_elem is not None:
                line_rate = coverage_elem.get('line-rate', '0')
                return float(line_rate) * 100
            
        except Exception as e:
            print(f"⚠️ Could not parse coverage report: {e}")
        
        return 0.0
    
    async def _generate_reports(self):
        """Generate comprehensive test reports."""
        
        print("\n📄 Generating test reports...")
        
        # Generate JSON summary report
        summary_report = {
            "test_execution": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": self.results.duration_seconds,
                "environment": self.config.environment,
                "configuration": {
                    "test_types": self.config.test_types,
                    "parallel_workers": self.config.parallel_workers,
                    "coverage_threshold": self.config.coverage_threshold
                }
            },
            "results": {
                "total_tests": self.results.total_tests,
                "passed_tests": self.results.passed_tests,
                "failed_tests": self.results.failed_tests,
                "skipped_tests": self.results.skipped_tests,
                "success_rate": (self.results.passed_tests / self.results.total_tests * 100) if self.results.total_tests > 0 else 0,
                "coverage_percentage": self.results.coverage_percentage,
                "exit_code": self.results.exit_code
            },
            "failures": self.results.failed_test_details,
            "performance_metrics": await self._collect_performance_metrics()
        }
        
        # Save summary report
        summary_file = self.reports_dir / "test_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary_report, f, indent=2)
        
        # Generate HTML dashboard
        await self._generate_html_dashboard(summary_report)
        
        print(f"✅ Reports generated in {self.reports_dir}")
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics during testing."""
        
        return {
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "disk_usage_percent": psutil.disk_usage('.').percent
            },
            "resource_usage": {
                "peak_memory_mb": psutil.Process().memory_info().rss / (1024**2),
                "avg_cpu_percent": psutil.cpu_percent(interval=1)
            }
        }
    
    async def _generate_html_dashboard(self, summary_data: Dict[str, Any]):
        """Generate HTML test dashboard."""
        
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .success { background: #d4edda; border-color: #c3e6cb; }
        .warning { background: #fff3cd; border-color: #ffeaa7; }
        .danger { background: #f8d7da; border-color: #f5c6cb; }
        .chart { margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Test Execution Dashboard</h1>
        <p>Execution completed at: {end_time}</p>
        <p>Duration: {duration:.1f} seconds</p>
    </div>
    
    <div class="metrics">
        <div class="metric {success_class}">
            <h3>Total Tests</h3>
            <p style="font-size: 24px; margin: 0;">{total_tests}</p>
        </div>
        
        <div class="metric success">
            <h3>Passed</h3>
            <p style="font-size: 24px; margin: 0; color: green;">{passed_tests}</p>
        </div>
        
        <div class="metric {failed_class}">
            <h3>Failed</h3>
            <p style="font-size: 24px; margin: 0; color: red;">{failed_tests}</p>
        </div>
        
        <div class="metric">
            <h3>Coverage</h3>
            <p style="font-size: 24px; margin: 0;">{coverage:.1f}%</p>
        </div>
    </div>
    
    <h2>📊 Test Results by Suite</h2>
    <table>
        <tr>
            <th>Test Suite</th>
            <th>Status</th>
            <th>Duration</th>
            <th>Report</th>
        </tr>
        {suite_rows}
    </table>
    
    <h2>🔧 System Information</h2>
    <p>CPU Cores: {cpu_count}</p>
    <p>Memory: {memory_gb:.1f} GB</p>
    <p>Peak Memory Usage: {peak_memory_mb:.1f} MB</p>
    
</body>
</html>
        """
        
        # Prepare template variables
        results = summary_data["results"]
        system_info = summary_data["performance_metrics"]["system_info"]
        
        success_class = "success" if results["failed_tests"] == 0 else "danger"
        failed_class = "danger" if results["failed_tests"] > 0 else "success"
        
        suite_rows = ""
        for test_type in self.config.test_types:
            status = "✅ PASSED" if test_type not in [f["test_type"] for f in self.results.failed_test_details] else "❌ FAILED"
            suite_rows += f"""
            <tr>
                <td>{test_type.upper()}</td>
                <td>{status}</td>
                <td>-</td>
                <td><a href="{test_type}_report.html">View Report</a></td>
            </tr>
            """
        
        # Generate HTML
        html_content = html_template.format(
            end_time=summary_data["test_execution"]["end_time"],
            duration=summary_data["test_execution"]["duration_seconds"],
            total_tests=results["total_tests"],
            passed_tests=results["passed_tests"],
            failed_tests=results["failed_tests"],
            coverage=results["coverage_percentage"],
            success_class=success_class,
            failed_class=failed_class,
            suite_rows=suite_rows,
            cpu_count=system_info["cpu_count"],
            memory_gb=system_info["memory_total_gb"],
            peak_memory_mb=summary_data["performance_metrics"]["resource_usage"]["peak_memory_mb"]
        )
        
        # Save HTML dashboard
        dashboard_file = self.reports_dir / "dashboard.html"
        with open(dashboard_file, 'w') as f:
            f.write(html_content)
    
    async def _cleanup_test_environment(self):
        """Cleanup test environment after execution."""
        
        print("🧹 Cleaning up test environment...")
        
        # Remove temporary test data
        test_data_dir = Path("test-data")
        if test_data_dir.exists():
            import shutil
            shutil.rmtree(test_data_dir)
        
        # Clear test cache
        pytest_cache = Path(".pytest_cache")
        if pytest_cache.exists():
            import shutil
            shutil.rmtree(pytest_cache)
        
        print("✅ Cleanup complete")
    
    def _print_summary(self):
        """Print test execution summary."""
        
        print("\n" + "=" * 60)
        print("🎉 TEST EXECUTION SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests:     {self.results.total_tests}")
        print(f"Passed:          {self.results.passed_tests} ✅")
        print(f"Failed:          {self.results.failed_tests} ❌")
        print(f"Skipped:         {self.results.skipped_tests} ⏭️")
        print(f"Duration:        {self.results.duration_seconds:.1f} seconds")
        print(f"Coverage:        {self.results.coverage_percentage:.1f}%")
        
        if self.results.total_tests > 0:
            success_rate = (self.results.passed_tests / self.results.total_tests) * 100
            print(f"Success Rate:    {success_rate:.1f}%")
        
        # Coverage validation
        if self.results.coverage_percentage < self.config.coverage_threshold * 100:
            print(f"⚠️ Coverage below threshold ({self.config.coverage_threshold:.1%})")
            self.results.exit_code = 1
        
        # Print failed test details
        if self.results.failed_test_details:
            print("\n❌ FAILED TEST DETAILS:")
            print("-" * 40)
            for failure in self.results.failed_test_details:
                print(f"  {failure['test_type'].upper()}: {failure['failed_count']} failures")
                if failure.get('error'):
                    print(f"    Error: {failure['error'][:100]}...")
        
        print(f"\n📄 Reports available in: {self.reports_dir}")
        print(f"🌐 Dashboard: {self.reports_dir}/dashboard.html")
        
        if self.results.exit_code == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n💥 TESTS FAILED (Exit Code: {self.results.exit_code})")
        
        print("=" * 60)


# ================================================================================================
# 🚀 CLI INTERFACE
# ================================================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for semiconductor manufacturing platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit --integration
  python run_tests.py --all --parallel 4 --coverage 0.85
  python run_tests.py --e2e --verbose --no-cleanup
  python run_tests.py --performance --security --timeout 3600
        """
    )
    
    # Test selection
    test_group = parser.add_argument_group("Test Selection")
    test_group.add_argument("--all", action="store_true", help="Run all test suites")
    test_group.add_argument("--unit", action="store_true", help="Run unit tests")
    test_group.add_argument("--integration", action="store_true", help="Run integration tests")
    test_group.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    test_group.add_argument("--performance", action="store_true", help="Run performance tests")
    test_group.add_argument("--security", action="store_true", help="Run security tests")
    test_group.add_argument("--compliance", action="store_true", help="Run compliance tests")
    
    # Execution options
    exec_group = parser.add_argument_group("Execution Options")
    exec_group.add_argument("--parallel", "-p", type=int, default=4, help="Number of parallel workers")
    exec_group.add_argument("--timeout", "-t", type=int, default=3600, help="Overall timeout in seconds")
    exec_group.add_argument("--fast-fail", "-x", action="store_true", help="Stop on first failure")
    exec_group.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Coverage options
    coverage_group = parser.add_argument_group("Coverage Options")
    coverage_group.add_argument("--coverage", "-c", type=float, default=0.80, help="Minimum coverage threshold")
    
    # Environment options
    env_group = parser.add_argument_group("Environment Options")
    env_group.add_argument("--env", default="test", choices=["test", "ci", "local"], help="Test environment")
    env_group.add_argument("--no-cleanup", action="store_true", help="Skip cleanup after tests")
    
    # Reporting options
    report_group = parser.add_argument_group("Reporting Options")
    report_group.add_argument("--reports", nargs="+", default=["html", "xml", "json"], 
                             choices=["html", "xml", "json"], help="Report formats")
    
    return parser


async def main():
    """Main test runner entry point."""
    
    parser = create_parser()
    args = parser.parse_args()
    
    # Determine test types to run
    test_types = []
    if args.all:
        test_types = list(TEST_SUITES.keys())
    else:
        if args.unit:
            test_types.append("unit")
        if args.integration:
            test_types.append("integration")
        if args.e2e:
            test_types.append("e2e")
        if args.performance:
            test_types.append("performance")
        if args.security:
            test_types.append("security")
        if args.compliance:
            test_types.append("compliance")
    
    if not test_types:
        print("❌ No test types specified. Use --help for options.")
        sys.exit(1)
    
    # Create configuration
    config = TestConfig(
        test_types=test_types,
        parallel_workers=args.parallel,
        coverage_threshold=args.coverage,
        timeout_seconds=args.timeout,
        environment=args.env,
        report_formats=args.reports,
        failure_threshold=0.05,  # 5% failure threshold
        verbose=args.verbose,
        fast_fail=args.fast_fail,
        cleanup_after=not args.no_cleanup
    )
    
    # Run tests
    runner = TestRunner(config)
    results = await runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(results.exit_code)


if __name__ == "__main__":
    asyncio.run(main())