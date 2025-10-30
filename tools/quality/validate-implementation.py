#!/usr/bin/env python3
"""
Implementation Completeness Validator

Validates that an issue implementation is genuinely complete before
allowing it to be marked as done or merged.

Usage:
    python validate-implementation.py --issue issues/001-database-models.md
    python validate-implementation.py --issue issues/002-auth.md --strict
"""

import sys
import subprocess
import json
import re
import ast
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import argparse


class ImplementationValidator:
    """Comprehensive implementation validation system."""
    
    def __init__(self, issue_file: Path, strict_mode: bool = False):
        self.issue_file = issue_file
        self.strict_mode = strict_mode
        self.project_root = Path(__file__).parent.parent.parent
        self.errors = []
        self.warnings = []
        self.validations_run = []
        
    def parse_issue_file(self) -> Dict[str, Any]:
        """Parse issue markdown file to extract requirements."""
        if not self.issue_file.exists():
            self.errors.append(f"Issue file not found: {self.issue_file}")
            return {}
            
        content = self.issue_file.read_text()
        
        # Extract implementation structure
        structure_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
        file_structure = []
        if structure_match:
            structure_lines = structure_match.group(1).split('\n')
            for line in structure_lines:
                if '.' in line and not line.strip().startswith('#'):
                    # Extract file paths from structure
                    path_match = re.search(r'[\w\-/]+\.\w+', line)
                    if path_match:
                        file_structure.append(path_match.group(0))
        
        # Extract acceptance criteria
        criteria_section = re.search(r'## 🎯 Acceptance Criteria(.*?)##', content, re.DOTALL)
        acceptance_criteria = []
        if criteria_section:
            criteria_text = criteria_section.group(1)
            criteria_matches = re.findall(r'- \[ \] \*\*(.*?)\*\*:', criteria_text)
            acceptance_criteria = criteria_matches
        
        # Extract technical specifications
        tech_specs = {}
        spec_matches = re.findall(r'### \d+\. (.*?)\n\n\*\*File\*\*: `(.*?)`', content, re.DOTALL)
        for spec_name, file_path in spec_matches:
            tech_specs[spec_name] = file_path
        
        return {
            'file_structure': file_structure,
            'acceptance_criteria': acceptance_criteria,
            'technical_specifications': tech_specs,
            'issue_title': self.extract_issue_title(content),
            'priority': self.extract_priority(content)
        }
    
    def extract_issue_title(self, content: str) -> str:
        """Extract issue title from markdown."""
        title_match = re.search(r'^# (.+)', content, re.MULTILINE)
        return title_match.group(1) if title_match else "Unknown Issue"
    
    def extract_priority(self, content: str) -> str:
        """Extract issue priority."""
        priority_match = re.search(r'\*\*(HIGH|MEDIUM|LOW)\*\*', content)
        return priority_match.group(1) if priority_match else "UNKNOWN"
    
    def validate_file_structure(self, issue_data: Dict[str, Any]) -> bool:
        """Verify all required files exist and are accessible."""
        self.validations_run.append("file_structure")
        missing_files = []
        invalid_files = []
        
        # Check files from implementation structure
        for file_path in issue_data.get('file_structure', []):
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            elif not full_path.is_file():
                invalid_files.append(f"{file_path} is not a file")
        
        # Check technical specification files
        for spec_name, file_path in issue_data.get('technical_specifications', {}).items():
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(f"{file_path} (from {spec_name})")
        
        if missing_files:
            self.errors.append(f"Missing required files: {missing_files}")
        if invalid_files:
            self.errors.append(f"Invalid file paths: {invalid_files}")
            
        return len(missing_files) == 0 and len(invalid_files) == 0
    
    def validate_python_syntax(self) -> bool:
        """Verify all Python files have valid syntax."""
        self.validations_run.append("python_syntax")
        syntax_errors = []
        
        # Find all Python files in the project
        python_files = list(self.project_root.glob('**/*.py'))
        
        for py_file in python_files:
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file.relative_to(self.project_root)}: {e}")
            except Exception as e:
                self.warnings.append(f"Could not parse {py_file.relative_to(self.project_root)}: {e}")
        
        if syntax_errors:
            self.errors.append(f"Python syntax errors: {syntax_errors}")
            return False
        return True
    
    def validate_imports(self) -> bool:
        """Verify critical imports resolve successfully."""
        self.validations_run.append("import_resolution")
        import_errors = []
        
        # Define critical imports to test based on issue type
        critical_imports = [
            "from services.shared.models import Part, Lot, Inspection, Defect",
            "from services.shared.database.base import BaseModel",
            "from services.shared.database.enums import PartTypeEnum",
        ]
        
        for import_stmt in critical_imports:
            try:
                result = subprocess.run(
                    [sys.executable, '-c', import_stmt],
                    capture_output=True, text=True,
                    cwd=self.project_root,
                    timeout=30
                )
                if result.returncode != 0:
                    import_errors.append(f"'{import_stmt}': {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                import_errors.append(f"'{import_stmt}': Import timeout")
            except Exception as e:
                import_errors.append(f"'{import_stmt}': {str(e)}")
        
        if import_errors:
            self.errors.append(f"Import resolution errors: {import_errors}")
            return False
        return True
    
    def validate_database_models(self) -> bool:
        """Verify database models are properly defined."""
        self.validations_run.append("database_models")
        model_errors = []
        
        # Check if models directory exists and has required files
        models_dir = self.project_root / "services/shared/models"
        if not models_dir.exists():
            self.errors.append("Models directory does not exist")
            return False
        
        required_model_files = [
            "manufacturing.py", "inspection.py", "inference.py", 
            "artifacts.py", "reporting.py", "audit.py"
        ]
        
        for model_file in required_model_files:
            model_path = models_dir / model_file
            if not model_path.exists():
                model_errors.append(f"Missing model file: {model_file}")
                continue
            
            # Check if the model file has class definitions
            try:
                with open(model_path, 'r') as f:
                    content = f.read()
                    if 'class' not in content or 'BaseModel' not in content:
                        model_errors.append(f"{model_file}: No model classes found")
            except Exception as e:
                model_errors.append(f"{model_file}: Error reading file - {e}")
        
        if model_errors:
            self.errors.append(f"Database model errors: {model_errors}")
            return False
        return True
    
    def validate_tests(self) -> Tuple[bool, float]:
        """Verify tests exist and pass, return coverage percentage."""
        self.validations_run.append("test_execution")
        
        # Find test files
        test_files = list(self.project_root.glob('**/test_*.py'))
        if not test_files:
            self.warnings.append("No test files found")
            return True, 0.0
        
        # Run tests with coverage
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', '--tb=short', '-v'],
                capture_output=True, text=True,
                cwd=self.project_root,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                self.errors.append(f"Tests failed: {result.stdout} {result.stderr}")
                return False, 0.0
            
            # Extract coverage percentage if available
            coverage_match = re.search(r'TOTAL.*?(\d+)%', result.stdout)
            coverage = float(coverage_match.group(1)) if coverage_match else 0.0
            
            return True, coverage
            
        except subprocess.TimeoutExpired:
            self.errors.append("Tests timed out after 5 minutes")
            return False, 0.0
        except Exception as e:
            self.errors.append(f"Error running tests: {e}")
            return False, 0.0
    
    def validate_api_contracts(self) -> bool:
        """Verify API endpoints are properly defined."""
        self.validations_run.append("api_contracts")
        
        # Find router files
        router_files = list(self.project_root.glob('**/routers/*.py'))
        api_errors = []
        
        for router_file in router_files:
            try:
                with open(router_file, 'r') as f:
                    content = f.read()
                    
                # Check for proper FastAPI router setup
                if 'APIRouter' not in content and 'FastAPI' not in content:
                    api_errors.append(f"{router_file.name}: No FastAPI router found")
                    
                # Check for proper HTTP method decorators
                http_methods = ['@router.get', '@router.post', '@router.put', '@router.delete']
                if not any(method in content for method in http_methods):
                    api_errors.append(f"{router_file.name}: No HTTP method decorators found")
                    
            except Exception as e:
                api_errors.append(f"{router_file.name}: Error reading file - {e}")
        
        if api_errors:
            self.errors.append(f"API contract errors: {api_errors}")
            return False
        return True
    
    def check_acceptance_criteria_implementation(self, issue_data: Dict[str, Any]) -> List[str]:
        """Check which acceptance criteria are implemented."""
        implemented_criteria = []
        
        for criterion in issue_data.get('acceptance_criteria', []):
            # Simple heuristic checks for common criteria
            if 'SQLAlchemy Models' in criterion:
                models_dir = self.project_root / "services/shared/models"
                if models_dir.exists() and any(models_dir.glob('*.py')):
                    implemented_criteria.append(criterion)
            elif 'Database Session Management' in criterion:
                session_file = self.project_root / "services/shared/database/session.py"
                if session_file.exists():
                    implemented_criteria.append(criterion)
            elif 'Alembic Migrations' in criterion:
                migrations_dir = self.project_root / "services/shared/migrations"
                if migrations_dir.exists():
                    implemented_criteria.append(criterion)
            # Add more criteria checks as needed
        
        return implemented_criteria
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        start_time = datetime.now()
        
        # Parse issue requirements
        issue_data = self.parse_issue_file()
        if not issue_data and self.errors:
            return self.generate_report(start_time, 0.0, [])
        
        # Run all validations
        file_structure_valid = self.validate_file_structure(issue_data)
        syntax_valid = self.validate_python_syntax()
        imports_valid = self.validate_imports()
        models_valid = self.validate_database_models()
        tests_valid, coverage = self.validate_tests()
        api_valid = self.validate_api_contracts()
        
        # Check acceptance criteria
        implemented_criteria = self.check_acceptance_criteria_implementation(issue_data)
        
        return self.generate_report(start_time, coverage, implemented_criteria)
    
    def generate_report(self, start_time: datetime, coverage: float, implemented_criteria: List[str]) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        is_complete = len(self.errors) == 0
        
        return {
            "validation_metadata": {
                "issue_file": str(self.issue_file),
                "validation_time": end_time.isoformat(),
                "duration_seconds": round(duration, 2),
                "strict_mode": self.strict_mode,
                "validator_version": "1.0.0"
            },
            "validation_summary": {
                "is_complete": is_complete,
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "validations_run": self.validations_run,
                "test_coverage_percentage": coverage
            },
            "validation_details": {
                "errors": self.errors,
                "warnings": self.warnings,
                "implemented_criteria": implemented_criteria
            },
            "quality_score": self.calculate_quality_score(coverage),
            "recommendation": self.generate_recommendation(is_complete, coverage),
            "next_steps": self.generate_next_steps()
        }
    
    def calculate_quality_score(self, coverage: float) -> float:
        """Calculate overall quality score (0-100)."""
        base_score = 100.0
        
        # Deduct for errors (20 points per error)
        base_score -= len(self.errors) * 20
        
        # Deduct for warnings (5 points per warning)
        base_score -= len(self.warnings) * 5
        
        # Factor in test coverage
        coverage_score = coverage * 0.3  # 30% weight on coverage
        base_score = (base_score * 0.7) + coverage_score
        
        return max(0.0, min(100.0, round(base_score, 2)))
    
    def generate_recommendation(self, is_complete: bool, coverage: float) -> str:
        """Generate implementation recommendation."""
        if is_complete and coverage >= 90:
            return "✅ Implementation is complete and meets quality standards - ready for merge"
        elif is_complete and coverage >= 70:
            return "🟡 Implementation is functionally complete but test coverage could be improved"
        elif is_complete:
            return "🟡 Implementation is functionally complete but has quality concerns"
        else:
            return "❌ Implementation is incomplete - resolve errors before proceeding"
    
    def generate_next_steps(self) -> List[str]:
        """Generate actionable next steps."""
        steps = []
        
        if self.errors:
            steps.append("🔴 Fix all validation errors listed above")
        
        if len(self.warnings) > 5:
            steps.append("🟡 Address validation warnings to improve code quality")
        
        if "test_execution" not in self.validations_run:
            steps.append("🔵 Run test suite to verify functionality")
        
        if not steps:
            steps.append("✅ All validations passed - ready for final review")
        
        return steps


def main():
    parser = argparse.ArgumentParser(description="Validate implementation completeness")
    parser.add_argument("--issue", required=True, help="Path to issue markdown file")
    parser.add_argument("--strict", action="store_true", help="Enable strict validation mode")
    parser.add_argument("--output", help="Output validation report to JSON file")
    parser.add_argument("--quiet", action="store_true", help="Only output final result")
    
    args = parser.parse_args()
    
    issue_path = Path(args.issue)
    if not issue_path.exists():
        # Try to find the issue file by number
        if issue_path.name.isdigit():
            issue_pattern = f"{int(issue_path.name):03d}-*.md"
            possible_files = list(Path("issues").glob(issue_pattern))
            if possible_files:
                issue_path = possible_files[0]
            else:
                print(f"❌ Issue file not found: {args.issue}", file=sys.stderr)
                sys.exit(1)
    
    validator = ImplementationValidator(issue_path, args.strict)
    report = validator.run_validation()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
    
    if not args.quiet:
        print(json.dumps(report, indent=2))
    else:
        print(report["recommendation"])
    
    # Exit with appropriate code
    sys.exit(0 if report["validation_summary"]["is_complete"] else 1)


if __name__ == "__main__":
    main()