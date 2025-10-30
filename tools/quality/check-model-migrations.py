#!/usr/bin/env python3
"""
Database model migration consistency checker.
Ensures SQLAlchemy models are properly defined and migrations are consistent.
"""

import ast
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Set
import importlib.util


class ModelMigrationValidator:
    """Validates database model consistency and migration requirements."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.validated_models = 0
        self.model_definitions = {}
    
    def validate_model_definition(self, source_code: str, file_path: str) -> None:
        """Validate SQLAlchemy model definitions."""
        tree = ast.parse(source_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a SQLAlchemy model
                is_sqlalchemy_model = any(
                    (isinstance(base, ast.Name) and base.id in ['BaseModel', 'Base']) or
                    (isinstance(base, ast.Attribute) and base.attr in ['BaseModel', 'Base'])
                    for base in node.bases
                )
                
                if is_sqlalchemy_model:
                    self.validated_models += 1
                    model_name = node.name
                    
                    # Store model definition for cross-reference
                    self.model_definitions[model_name] = {
                        'file': file_path,
                        'line': node.lineno,
                        'columns': [],
                        'relationships': [],
                        'table_name': None
                    }
                    
                    # Validate table name
                    has_tablename = any(
                        isinstance(item, ast.Assign) and
                        any(isinstance(target, ast.Name) and target.id == '__tablename__' 
                            for target in item.targets)
                        for item in node.body
                    )
                    
                    if not has_tablename:
                        self.errors.append(
                            f"{file_path}:{node.lineno} - Model '{model_name}' missing __tablename__"
                        )
                    
                    # Validate primary key
                    has_primary_key = False
                    
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    # Check for Column definitions
                                    if isinstance(item.value, ast.Call):
                                        call_name = self._get_call_name(item.value)
                                        if call_name == 'Column':
                                            column_name = target.id
                                            self.model_definitions[model_name]['columns'].append(column_name)
                                            
                                            # Check for primary key
                                            if self._has_primary_key_arg(item.value):
                                                has_primary_key = True
                                        
                                        elif call_name in ['relationship', 'backref']:
                                            self.model_definitions[model_name]['relationships'].append(target.id)
                    
                    if not has_primary_key:
                        self.errors.append(
                            f"{file_path}:{node.lineno} - Model '{model_name}' missing primary key"
                        )
                    
                    # Check for UUID primary key (recommended)
                    has_uuid_pk = any(
                        isinstance(item, ast.Assign) and
                        any(isinstance(target, ast.Name) and target.id == 'id' 
                            for target in item.targets) and
                        self._is_uuid_column(item.value)
                        for item in node.body
                    )
                    
                    if not has_uuid_pk:
                        self.warnings.append(
                            f"{file_path}:{node.lineno} - Model '{model_name}' should use UUID primary key"
                        )
                    
                    # Check for audit fields
                    audit_fields = ['created_at', 'updated_at']
                    model_columns = self.model_definitions[model_name]['columns']
                    
                    for audit_field in audit_fields:
                        if audit_field not in model_columns:
                            self.warnings.append(
                                f"{file_path}:{node.lineno} - Model '{model_name}' missing audit field '{audit_field}'"
                            )
    
    def _get_call_name(self, call_node: ast.Call) -> str:
        """Extract the name of a function call."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return ""
    
    def _has_primary_key_arg(self, call_node: ast.Call) -> bool:
        """Check if a Column call has primary_key=True."""
        for keyword in call_node.keywords:
            if keyword.arg == 'primary_key':
                if isinstance(keyword.value, ast.Constant):
                    return keyword.value.value is True
                elif isinstance(keyword.value, ast.NameConstant):
                    return keyword.value.value is True
        return False
    
    def _is_uuid_column(self, call_node: ast.Call) -> bool:
        """Check if a Column uses UUID type."""
        if not isinstance(call_node, ast.Call):
            return False
        
        # Check if first argument is UUID type
        if call_node.args:
            first_arg = call_node.args[0]
            if isinstance(first_arg, ast.Name) and first_arg.id == 'UUID':
                return True
            elif isinstance(first_arg, ast.Attribute) and first_arg.attr == 'UUID':
                return True
        
        return False
    
    def validate_relationship_consistency(self) -> None:
        """Validate that relationships between models are consistent."""
        for model_name, model_info in self.model_definitions.items():
            for relationship in model_info['relationships']:
                # Check if related model exists
                # This is a simplified check - in a full implementation,
                # we would parse the relationship arguments to find the target model
                pass
    
    def validate_file(self, file_path: Path) -> None:
        """Validate a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            self.validate_model_definition(source_code, str(file_path))
            
        except Exception as e:
            self.errors.append(f"Error processing {file_path}: {e}")
    
    def validate_directory(self, directory: Path) -> None:
        """Validate all Python files in a directory."""
        for python_file in directory.rglob("*.py"):
            # Skip test files and __pycache__
            if "test" in python_file.name or "__pycache__" in str(python_file):
                continue
            
            self.validate_file(python_file)
        
        # After processing all files, validate cross-references
        self.validate_relationship_consistency()
    
    def check_migration_status(self) -> None:
        """Check if migrations are up to date."""
        # This would typically check Alembic migration status
        # For now, we'll just warn if there are many models without recent migrations
        if self.validated_models > 5:
            self.warnings.append(
                f"Found {self.validated_models} models - ensure migrations are up to date"
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            'validated_models': self.validated_models,
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'model_definitions': self.model_definitions,
            'success': len(self.errors) == 0
        }


def main():
    """Main function for model migration validation."""
    parser = argparse.ArgumentParser(description='Validate database model migrations')
    parser.add_argument('--directory', '-d', type=Path, default=Path('services/shared/models'),
                       help='Directory to validate')
    parser.add_argument('--check-migrations', action='store_true',
                       help='Check migration status')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    print("🗃️  Validating database models...")
    
    validator = ModelMigrationValidator()
    
    if args.directory.is_file():
        validator.validate_file(args.directory)
    elif args.directory.is_dir():
        validator.validate_directory(args.directory)
    else:
        print(f"❌ Path not found: {args.directory}")
        sys.exit(1)
    
    if args.check_migrations:
        validator.check_migration_status()
    
    summary = validator.get_summary()
    
    # Print results
    print(f"📊 Validation completed:")
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
    
    if args.verbose and summary['model_definitions']:
        print(f"\n📋 Models found:")
        for model_name, model_info in summary['model_definitions'].items():
            print(f"  - {model_name} ({len(model_info['columns'])} columns, {len(model_info['relationships'])} relationships)")
    
    # Determine exit code
    if summary['total_errors'] > 0:
        print("❌ Model validation failed")
        sys.exit(1)
    else:
        print("✅ Model validation passed")
        sys.exit(0)


if __name__ == '__main__':
    main()