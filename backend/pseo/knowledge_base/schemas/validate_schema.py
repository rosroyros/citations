#!/usr/bin/env python3
"""
JSON Schema validation script for PSEO knowledge base.
Validates all data files against their respective schemas.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import argparse

try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    print("Installing jsonschema...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "jsonschema"])
    import jsonschema
    from jsonschema import validate, ValidationError


class SchemaValidator:
    """Validates JSON files against schemas."""

    def __init__(self, schemas_dir: str = None):
        if schemas_dir is None:
            schemas_dir = Path(__file__).parent
        self.schemas_dir = Path(schemas_dir)
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, Dict]:
        """Load all schema files."""
        schemas = {}
        schema_files = {
            'citation_rule': 'citation_rule_schema.json',
            'citation_rules': 'citation_rules_schema.json',
            'source_type': 'source_type_schema.json',
            'error': 'error_schema.json',
            'common_errors': 'common_errors_schema.json',
            'example': 'example_schema.json',
            'examples': 'examples_schema.json'
        }

        for schema_type, filename in schema_files.items():
            schema_path = self.schemas_dir / filename
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schemas[schema_type] = json.load(f)
            else:
                raise FileNotFoundError(f"Schema file not found: {schema_path}")

        return schemas

    def validate_file(self, file_path: str, data_type: str) -> Dict[str, Any]:
        """Validate a single JSON file against its schema."""
        result = {
            'file': file_path,
            'valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Get the appropriate schema
            if data_type not in self.schemas:
                result['errors'].append(f"Unknown data type: {data_type}")
                return result

            schema = self.schemas[data_type]

            # Validate against schema
            validate(instance=data, schema=schema)

            # Additional custom validations
            warnings = self._custom_validations(data, data_type)
            result['warnings'].extend(warnings)

            result['valid'] = True

        except FileNotFoundError:
            result['errors'].append(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            result['errors'].append(f"Invalid JSON: {e}")
        except ValidationError as e:
            result['errors'].append(f"Schema validation failed: {e.message}")
            if e.absolute_path:
                location = " -> ".join(str(p) for p in e.absolute_path)
                result['errors'].append(f"Location: {location}")
        except Exception as e:
            result['errors'].append(f"Unexpected error: {e}")

        return result

    def _custom_validations(self, data: Any, data_type: str) -> List[str]:
        """Perform custom validations beyond JSON schema."""
        warnings = []

        if data_type == 'citation_rule':
            # Check that examples include both correct and incorrect
            if isinstance(data, dict) and 'examples' in data:
                examples = data['examples']
                has_correct = any(ex.get('type') == 'correct' for ex in examples)
                has_incorrect = any(ex.get('type') == 'incorrect' for ex in examples)

                if not has_correct:
                    warnings.append("Rule should include at least one correct example")
                if not has_incorrect:
                    warnings.append("Rule should include at least one incorrect example")

                # Check if any correct and incorrect examples are identical
                correct_examples = [ex.get('example', '') for ex in examples if ex.get('type') == 'correct']
                incorrect_examples = [ex.get('example', '') for ex in examples if ex.get('type') == 'incorrect']

                for correct in correct_examples:
                    for incorrect in incorrect_examples:
                        if correct == incorrect and correct:
                            warnings.append("Correct and incorrect examples should be different")

        elif data_type == 'example':
            # Check DOI format if present
            if isinstance(data, dict) and 'metadata' in data:
                metadata = data['metadata']
                if 'source' in metadata and 'doi' in metadata['source']:
                    doi = metadata['source']['doi']
                    if not doi.startswith('10.'):
                        warnings.append(f"DOI should start with '10.': {doi}")

        elif data_type == 'error':
            # Check that wrong and right examples are actually different
            if isinstance(data, dict):
                wrong = data.get('wrong_example', '')
                correct = data.get('correct_example', '')
                if wrong == correct:
                    warnings.append("Wrong and correct examples should be different")

  
        return warnings

    def validate_directory(self, data_dir: str, data_type: str) -> Dict[str, Any]:
        """Validate all JSON files of a specific type in a directory."""
        data_path = Path(data_dir)
        if not data_path.exists():
            return {
                'directory': data_dir,
                'valid': False,
                'errors': [f"Directory not found: {data_dir}"],
                'files': []
            }

        results = {
            'directory': data_dir,
            'data_type': data_type,
            'valid': True,
            'total_files': 0,
            'valid_files': 0,
            'files': []
        }

        # Find all JSON files
        json_files = list(data_path.glob("*.json"))
        results['total_files'] = len(json_files)

        for json_file in json_files:
            file_result = self.validate_file(str(json_file), data_type)
            results['files'].append(file_result)

            if file_result['valid']:
                results['valid_files'] += 1
            else:
                results['valid'] = False

        return results

    def validate_all(self, knowledge_base_dir: str) -> Dict[str, Any]:
        """Validate all knowledge base files."""
        kb_path = Path(knowledge_base_dir)

        all_results = {
            'knowledge_base': knowledge_base_dir,
            'valid': True,
            'summary': {},
            'details': {}
        }

        # Expected files and their types
        expected_files = {
            'citation_rules.json': 'citation_rules',
            'examples.json': 'examples'
        }

        # Optional files
        optional_files = {
            'source_types.json': 'source_type',
            'common_errors.json': 'common_errors'
        }

        for filename, data_type in expected_files.items():
            file_path = kb_path / filename
            if file_path.exists():
                result = self.validate_file(str(file_path), data_type)
                all_results['details'][filename] = result

                if not result['valid']:
                    all_results['valid'] = False
            else:
                all_results['details'][filename] = {
                    'file': str(file_path),
                    'valid': False,
                    'errors': [f"Expected file not found: {filename}"],
                    'warnings': []
                }
                all_results['valid'] = False

        # Check optional files
        for filename, data_type in optional_files.items():
            file_path = kb_path / filename
            if file_path.exists():
                result = self.validate_file(str(file_path), data_type)
                all_results['details'][filename] = result
                # Optional files don't affect overall validity

        # Summary
        total_files = len(all_results['details'])
        valid_files = sum(1 for r in all_results['details'].values() if r['valid'])

        all_results['summary'] = {
            'total_files': total_files,
            'valid_files': valid_files,
            'invalid_files': total_files - valid_files
        }

        return all_results


def main():
    parser = argparse.ArgumentParser(description='Validate PSEO knowledge base JSON files')
    parser.add_argument('--file', '-f', help='Validate single file (specify type with --type)')
    parser.add_argument('--type', '-t', choices=['citation_rule', 'source_type', 'error', 'example'],
                       help='Type of data being validated')
    parser.add_argument('--directory', '-d', help='Validate directory of files (specify type with --type)')
    parser.add_argument('--knowledge-base', '-k', default='knowledge_base',
                       help='Validate complete knowledge base directory (default: knowledge_base)')
    parser.add_argument('--schemas-dir', '-s', help='Schemas directory (default: same as script)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Initialize validator
    try:
        validator = SchemaValidator(args.schemas_dir)
    except Exception as e:
        print(f"Error initializing validator: {e}")
        sys.exit(1)

    # Perform validation based on arguments
    if args.file:
        if not args.type:
            print("Error: --type required when validating single file")
            sys.exit(1)

        result = validator.validate_file(args.file, args.type)
        print(f"\nValidating: {result['file']}")
        print(f"Result: {'✅ VALID' if result['valid'] else '❌ INVALID'}")

        if result['errors']:
            print("\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")

        if result['warnings'] and args.verbose:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")

    elif args.directory:
        if not args.type:
            print("Error: --type required when validating directory")
            sys.exit(1)

        result = validator.validate_directory(args.directory, args.type)
        print(f"\nValidating directory: {result['directory']}")
        print(f"Type: {result['data_type']}")
        print(f"Result: {'✅ ALL VALID' if result['valid'] else '❌ SOME INVALID'}")
        print(f"Files: {result['valid_files']}/{result['total_files']} valid")

        if not result['valid'] and args.verbose:
            print("\nInvalid files:")
            for file_result in result['files']:
                if not file_result['valid']:
                    print(f"  - {Path(file_result['file']).name}")
                    for error in file_result['errors']:
                        print(f"    {error}")

    else:
        # Validate complete knowledge base
        result = validator.validate_all(args.knowledge_base)
        print(f"\nValidating knowledge base: {result['knowledge_base']}")
        print(f"Result: {'✅ ALL VALID' if result['valid'] else '❌ SOME INVALID'}")
        print(f"Files: {result['summary']['valid_files']}/{result['summary']['total_files']} valid")

        if not result['valid']:
            print("\nInvalid files:")
            for filename, file_result in result['details'].items():
                if not file_result['valid']:
                    print(f"  - {filename}")
                    for error in file_result['errors']:
                        print(f"    {error}")

        if args.verbose:
            print("\nDetailed results:")
            for filename, file_result in result['details'].items():
                status = "✅ VALID" if file_result['valid'] else "❌ INVALID"
                print(f"  {filename}: {status}")
                if file_result['warnings']:
                    for warning in file_result['warnings']:
                        print(f"    Warning: {warning}")

    # Exit with appropriate code
    sys.exit(0 if result.get('valid', False) else 1)


if __name__ == '__main__':
    main()