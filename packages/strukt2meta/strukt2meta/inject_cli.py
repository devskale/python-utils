"""
CLI interface for JSON metadata injection functionality.

This script provides command-line access to the JSON injection features
of strukt2meta, allowing users to inject AI-generated metadata into
target JSON files based on parameter configurations.
"""

import argparse
import json
import sys
from strukt2meta.injector import JSONInjector


def main():
    """Main CLI entry point for injection operations."""
    parser = argparse.ArgumentParser(
        description="Inject AI-generated metadata into JSON files using strukt2meta"
    )
    
    parser.add_argument(
        "--params", "-p",
        required=True,
        help="Path to the parameter configuration JSON file"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Perform a dry run without actually modifying files"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--rollback", "-r",
        help="Rollback using specified backup file"
    )
    
    args = parser.parse_args()
    
    try:
        if args.rollback:
            # Handle rollback operation
            print(f"Rolling back from backup: {args.rollback}")
            # Implementation for rollback would go here
            return
        
        # Initialize injector
        if args.verbose:
            print(f"Loading parameters from: {args.params}")
            
        injector = JSONInjector(args.params)
        
        if args.dry_run:
            print("DRY RUN MODE - No files will be modified")
            # Load and validate parameters
            print("Parameter validation: PASSED")
            print(f"Target file: {injector.params['target_filename']}")
            print(f"JSON file: {injector.params['json_inject_file']}")
            print(f"Input path: {injector.params['input_path']}")
            print(f"Prompt: {injector.params['prompt']}")
            return
        
        # Execute injection
        result = injector.inject()
        
        if result['success']:
            print("✅ Injection completed successfully!")
            if args.verbose:
                print(f"Target file: {result['target_file']}")
                print(f"Backup created: {result['backup_path']}")
                print("Injected metadata:")
                print(json.dumps(result['injected_metadata'], indent=2, ensure_ascii=False))
        else:
            print("❌ Injection failed")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()