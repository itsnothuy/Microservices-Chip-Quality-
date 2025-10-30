#!/usr/bin/env python3
"""
Quality gate checker for overall code quality validation.
Runs comprehensive checks before allowing commits/pushes.
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any
import json


class QualityGateChecker:
    """Comprehensive quality gate validation."""
    
    def __init__(self):
        self.results = {}
        self.overall_score = 0
        self.errors = []
        self.warnings = []
    
    def run_syntax_checks(self) -> Dict[str, Any]:
        """Run Python syntax validation."""
        print("🔍 Running syntax checks...")
        
        try:
            # Find all Python files
            python_files = list(Path('.').rglob('*.py'))
            python_files = [f for f in python_files if 'venv' not in str(f) and '__pycache__' not in str(f)]
            
            syntax_errors = []
            for file_path in python_files:
                try:
                    with open(file_path) as f:
                        compile(f.read(), str(file_path), 'exec')
                except SyntaxError as e:
                    syntax_errors.append(f"{file_path}:{e.lineno} - {e.msg}")
                except Exception as e:
                    syntax_errors.append(f"{file_path} - {e}")
            
            return {
                'success': len(syntax_errors) == 0,
                'errors': syntax_errors,
                'files_checked': len(python_files)
            }
        
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Syntax check failed: {e}"],
                'files_checked': 0
            }
    
    def run_import_checks(self) -> Dict[str, Any]:
        """Validate critical imports."""
        print("📦 Running import checks...")
        
        critical_imports = [
            'services.shared.models',
            'services.shared.database', 
            'services.shared.enums'
        ]
        
        import_errors = []
        successful_imports = []
        
        for module in critical_imports:
            try:
                result = subprocess.run([
                    sys.executable, '-c', f'import {module}'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    successful_imports.append(module)
                else:
                    import_errors.append(f"{module} - {result.stderr.strip()}")
            
            except Exception as e:
                import_errors.append(f"{module} - {e}")
        
        return {
            'success': len(import_errors) == 0,
            'errors': import_errors,
            'successful_imports': successful_imports,
            'total_imports': len(critical_imports)
        }
    
    def run_test_validation(self) -> Dict[str, Any]:
        """Run basic test validation."""
        print("🧪 Running test validation...")
        
        try:
            # Check if tests exist
            test_files = list(Path('.').rglob('test_*.py')) + list(Path('.').rglob('*_test.py'))
            
            if not test_files:
                return {
                    'success': False,
                    'errors': ['No test files found'],
                    'test_files': 0
                }
            
            # Run a quick test discovery
            result = subprocess.run([
                sys.executable, '-m', 'pytest', '--collect-only', '-q'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'errors': [f"Test discovery failed: {result.stderr}"],
                    'test_files': len(test_files)
                }
            
            return {
                'success': True,
                'errors': [],
                'test_files': len(test_files),
                'test_discovery': 'passed'
            }
        
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Test validation failed: {e}"],
                'test_files': 0
            }
    
    def run_structure_validation(self) -> Dict[str, Any]:
        """Validate project structure."""
        print("📁 Running structure validation...")
        
        required_dirs = [
            'services',
            'docs',
            'tests',
            'tools/quality'
        ]
        
        required_files = [
            'pyproject.toml',
            'README.md',
            '.gitignore',
            '.pre-commit-config.yaml'
        ]
        
        missing_dirs = []
        missing_files = []
        
        for dir_path in required_dirs:
            if not Path(dir_path).is_dir():
                missing_dirs.append(dir_path)
        
        for file_path in required_files:
            if not Path(file_path).is_file():
                missing_files.append(file_path)
        
        return {
            'success': len(missing_dirs) == 0 and len(missing_files) == 0,
            'missing_dirs': missing_dirs,
            'missing_files': missing_files,
            'required_dirs': len(required_dirs),
            'required_files': len(required_files)
        }
    
    def run_documentation_checks(self) -> Dict[str, Any]:
        """Check documentation completeness."""
        print("📚 Running documentation checks...")
        
        doc_files = list(Path('.').rglob('*.md'))
        doc_issues = []
        
        # Check README
        readme = Path('README.md')
        if readme.exists():
            with open(readme) as f:
                content = f.read()
                if len(content) < 500:
                    doc_issues.append("README.md is too short (< 500 characters)")
                if '# ' not in content:
                    doc_issues.append("README.md missing main heading")
        else:
            doc_issues.append("README.md not found")
        
        # Check for API documentation
        api_docs = list(Path('docs').rglob('*api*.md')) if Path('docs').exists() else []
        if not api_docs:
            doc_issues.append("No API documentation found in docs/")
        
        return {
            'success': len(doc_issues) == 0,
            'errors': doc_issues,
            'doc_files': len(doc_files),
            'api_docs': len(api_docs)
        }
    
    def calculate_quality_score(self) -> float:
        """Calculate overall quality score."""
        weights = {
            'syntax': 30,
            'imports': 25,
            'tests': 20,
            'structure': 15,
            'documentation': 10
        }
        
        total_score = 0
        total_weight = 0
        
        for check, weight in weights.items():
            if check in self.results:
                result = self.results[check]
                score = 100 if result['success'] else 0
                
                # Partial scoring for some checks
                if check == 'imports' and not result['success']:
                    # Partial score based on successful imports
                    successful = len(result.get('successful_imports', []))
                    total = result.get('total_imports', 1)
                    score = (successful / total) * 100
                
                elif check == 'structure' and not result['success']:
                    # Partial score based on missing items
                    missing_dirs = len(result.get('missing_dirs', []))
                    missing_files = len(result.get('missing_files', []))
                    required_dirs = result.get('required_dirs', 1)
                    required_files = result.get('required_files', 1)
                    
                    dirs_score = max(0, (required_dirs - missing_dirs) / required_dirs) * 50
                    files_score = max(0, (required_files - missing_files) / required_files) * 50
                    score = dirs_score + files_score
                
                total_score += score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all quality gate checks."""
        print("🚀 Running quality gate validation...\n")
        
        # Run individual checks
        self.results['syntax'] = self.run_syntax_checks()
        self.results['imports'] = self.run_import_checks()
        self.results['tests'] = self.run_test_validation()
        self.results['structure'] = self.run_structure_validation()
        self.results['documentation'] = self.run_documentation_checks()
        
        # Calculate overall score
        self.overall_score = self.calculate_quality_score()
        
        # Collect all errors and warnings
        for check, result in self.results.items():
            self.errors.extend(result.get('errors', []))
        
        return {
            'overall_score': self.overall_score,
            'success': self.overall_score >= 70 and len(self.errors) == 0,
            'results': self.results,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print validation summary."""
        score = summary['overall_score']
        success = summary['success']
        
        print(f"\n{'='*60}")
        print(f"🎯 QUALITY GATE SUMMARY")
        print(f"{'='*60}")
        
        status_emoji = "✅" if success else "❌"
        print(f"{status_emoji} Overall Status: {'PASSED' if success else 'FAILED'}")
        print(f"📊 Quality Score: {score:.1f}/100")
        
        # Score bar
        bar_length = 40
        filled = int((score / 100) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"📈 Progress: [{bar}] {score:.1f}%")
        
        print(f"\n📋 Individual Check Results:")
        for check, result in summary['results'].items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {check.capitalize():15} {status}")
        
        if summary['errors']:
            print(f"\n❌ Errors Found ({len(summary['errors'])}):")
            for error in summary['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(summary['errors']) > 10:
                print(f"  ... and {len(summary['errors']) - 10} more errors")
        
        if summary['warnings']:
            print(f"\n⚠️  Warnings ({len(summary['warnings'])}):")
            for warning in summary['warnings'][:5]:  # Show first 5 warnings
                print(f"  - {warning}")
        
        print(f"\n{'='*60}")
        
        if success:
            print("🎉 All quality gates passed! Ready for commit/merge.")
        else:
            print("🚫 Quality gates failed. Please fix issues before proceeding.")
        
        print(f"{'='*60}")


def main():
    """Main function for quality gate checking."""
    parser = argparse.ArgumentParser(description='Run quality gate validation')
    parser.add_argument('--min-score', type=float, default=70.0,
                       help='Minimum quality score required')
    parser.add_argument('--output', '-o', help='Output JSON results to file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    checker = QualityGateChecker()
    summary = checker.run_all_checks()
    
    # Print summary
    checker.print_summary(summary)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n💾 Results saved to {args.output}")
    
    # Determine exit code
    if summary['success'] and summary['overall_score'] >= args.min_score:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()