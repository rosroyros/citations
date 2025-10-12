#!/usr/bin/env python3
"""
Validation script for common errors JSON file
"""
import json
import sys
from pathlib import Path
from jsonschema import validate, ValidationError

def load_schema():
    """Load the error schema"""
    schema_file = Path(__file__).parent / "schemas" / "error_schema.json"
    with open(schema_file) as f:
        return json.load(f)

def validate_errors_json(errors_file_path):
    """Validate errors JSON against schema"""
    try:
        # Load schema
        schema = load_schema()

        # Load errors data
        with open(errors_file_path) as f:
            errors_data = json.load(f)

        # Validate each error entry
        validation_errors = []
        for i, error in enumerate(errors_data, 1):
            try:
                validate(instance=error, schema=schema)
                print(f"✓ Error {i}: {error['error_id']} - Valid")
            except ValidationError as e:
                validation_errors.append({
                    "error_number": i,
                    "error_id": error.get('error_id', 'unknown'),
                    "validation_error": str(e)
                })
                print(f"✗ Error {i}: {error.get('error_id', 'unknown')} - Invalid")

        # Summary
        print(f"\n{'='*50}")
        print(f"Validation Summary:")
        print(f"Total errors: {len(errors_data)}")
        print(f"Valid entries: {len(errors_data) - len(validation_errors)}")
        print(f"Invalid entries: {len(validation_errors)}")

        if validation_errors:
            print(f"\nValidation Errors:")
            for err in validation_errors:
                print(f"  {err['error_number']}. {err['error_id']}: {err['validation_error']}")
            return False
        else:
            print("All entries are valid!")
            return True

    except Exception as e:
        print(f"Validation failed: {e}")
        return False

if __name__ == "__main__":
    errors_file = Path(__file__).parent.parent.parent.parent / "apa7_common_citation_errors.json"

    if not errors_file.exists():
        print(f"Errors file not found: {errors_file}")
        sys.exit(1)

    success = validate_errors_json(errors_file)
    sys.exit(0 if success else 1)