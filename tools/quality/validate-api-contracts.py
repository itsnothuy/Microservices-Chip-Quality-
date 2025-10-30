#!/usr/bin/env python3
"""
API contract validation script.
Ensures FastAPI routes and Pydantic models follow contract specifications.
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Set
import importlib.util


class APIContractValidator:
    """Validates API contracts in FastAPI applications."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.validated_routes = 0
        self.validated_models = 0
    
    def validate_route_docstrings(self, source_code: str, file_path: str) -> None:
        """Validate that API routes have proper docstrings."""
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for FastAPI decorators
                has_route_decorator = any(
                    isinstance(decorator, ast.Attribute) and
                    hasattr(decorator.value, 'id') and
                    decorator.value.id in ['app', 'router'] and
                    decorator.attr in ['get', 'post', 'put', 'delete', 'patch']
                    for decorator in node.decorator_list
                    if isinstance(decorator, ast.Attribute)
                )
                
                if has_route_decorator:
                    self.validated_routes += 1
                    
                    # Check docstring
                    if not ast.get_docstring(node):
                        self.errors.append(
                            f"{file_path}:{node.lineno} - Route '{node.name}' missing docstring"
                        )
                    
                    # Check response model annotation
                    if not node.returns:
                        self.warnings.append(
                            f"{file_path}:{node.lineno} - Route '{node.name}' missing return type annotation"
                        )
    
    def validate_pydantic_models(self, source_code: str, file_path: str) -> None:
        """Validate Pydantic model definitions."""
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a Pydantic model
                is_pydantic_model = any(
                    (isinstance(base, ast.Name) and base.id == 'BaseModel') or
                    (isinstance(base, ast.Attribute) and base.attr == 'BaseModel')
                    for base in node.bases
                )
                
                if is_pydantic_model:
                    self.validated_models += 1
                    
                    # Check class docstring
                    if not ast.get_docstring(node):
                        self.errors.append(
                            f"{file_path}:{node.lineno} - Pydantic model '{node.name}' missing docstring"
                        )
                    
                    # Check for Config class
                    has_config = any(
                        isinstance(item, ast.ClassDef) and item.name == 'Config'
                        for item in node.body
                    )
                    
                    if not has_config:
                        self.warnings.append(
                            f"{file_path}:{node.lineno} - Pydantic model '{node.name}' missing Config class"
                        )
                    
                    # Check field annotations
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            field_name = item.target.id
                            if not item.annotation:
                                self.errors.append(
                                    f"{file_path}:{item.lineno} - Field '{field_name}' in model '{node.name}' missing type annotation"
                                )
    
    def validate_error_handling(self, source_code: str, file_path: str) -> None:
        """Validate proper error handling in API routes."""
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for FastAPI route decorators
                has_route_decorator = any(
                    isinstance(decorator, ast.Attribute) and
                    hasattr(decorator.value, 'id') and
                    decorator.value.id in ['app', 'router']
                    for decorator in node.decorator_list
                    if isinstance(decorator, ast.Attribute)
                )
                
                if has_route_decorator:
                    # Check for try-except blocks
                    has_exception_handling = any(
                        isinstance(stmt, ast.Try)
                        for stmt in ast.walk(node)
                    )
                    
                    if not has_exception_handling:
                        self.warnings.append(
                            f"{file_path}:{node.lineno} - Route '{node.name}' may benefit from explicit exception handling"
                        )
    
    def validate_file(self, file_path: Path) -> None:
        """Validate a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            self.validate_route_docstrings(source_code, str(file_path))
            self.validate_pydantic_models(source_code, str(file_path))
            self.validate_error_handling(source_code, str(file_path))
            
        except Exception as e:
            self.errors.append(f"Error processing {file_path}: {e}")
    
    def validate_directory(self, directory: Path) -> None:
        """Validate all Python files in a directory."""
        for python_file in directory.rglob("*.py"):
            # Skip test files and __pycache__
            if "test" in python_file.name or "__pycache__" in str(python_file):
                continue
            
            self.validate_file(python_file)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            'validated_routes': self.validated_routes,
            'validated_models': self.validated_models,
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'success': len(self.errors) == 0
        }


def main():
    """Main function for API contract validation."""
    parser = argparse.ArgumentParser(description='Validate API contracts')
    parser.add_argument('--directory', '-d', type=Path, default=Path('services'),
                       help='Directory to validate')
    parser.add_argument('--fail-on-warnings', action='store_true',
                       help='Fail validation if warnings are found')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    print("🔍 Validating API contracts...")
    
    validator = APIContractValidator()
    
    if args.directory.is_file():
        validator.validate_file(args.directory)
    elif args.directory.is_dir():
        validator.validate_directory(args.directory)
    else:
        print(f"❌ Path not found: {args.directory}")
        sys.exit(1)
    
    summary = validator.get_summary()
    
    # Print results
    print(f"📊 Validation completed:")
    print(f"  Routes validated: {summary['validated_routes']}")
    print(f"  Models validated: {summary['validated_models']}")
    print(f"  Errors: {summary['total_errors']}")
    print(f"  Warnings: {summary['total_warnings']}")
    
    if summary['errors']:
        print("\n❌ Errors found:")
        for error in summary['errors']:
            print(f"  - {error}")
    
    if summary['warnings'] and args.verbose:
        print("\n⚠️  Warnings:")
        for warning in summary['warnings']:
            print(f"  - {warning}")
    
    # Determine exit code
    if summary['total_errors'] > 0:
        print("❌ API contract validation failed")
        sys.exit(1)
    elif summary['total_warnings'] > 0 and args.fail_on_warnings:
        print("❌ API contract validation failed due to warnings")
        sys.exit(1)
    else:
        print("✅ API contract validation passed")
        sys.exit(0)


if __name__ == '__main__':
    main()