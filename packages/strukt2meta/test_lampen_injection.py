#!/usr/bin/env python3
"""
Test script for metadata injection in the Lampen (lighting) project.
This script demonstrates injecting metadata for a single file first.
"""

import os
import sys
import json
from pathlib import Path

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import the JSONInjector class
try:
    from strukt2meta.injector import JSONInjector
except ImportError:
    # Try importing from the strukt2meta subdirectory
    import importlib.util
    injector_path = os.path.join(current_dir, "strukt2meta", "injector.py")
    spec = importlib.util.spec_from_file_location("injector", injector_path)
    injector_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(injector_module)
    JSONInjector = injector_module.JSONInjector


def main():
    """Test metadata injection for the lighting project."""

    print("🔍 Testing Metadata Injection for Lampen Project")
    print("=" * 60)

    # Check if required files exist
    param_file = "lampen_injection_params.json"
    if not os.path.exists(param_file):
        print(f"❌ Parameter file not found: {param_file}")
        return

    # Load parameters
    with open(param_file, 'r', encoding='utf-8') as f:
        params = json.load(f)

    # Load config to show AI model
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    print(f"📄 Input document: {params['input_path']}")
    print(f"🎯 Target file: {params['target_filename']}")
    print(f"📊 JSON file: {params['json_inject_file']}")
    print(f"📝 Prompt: {params['prompt']}")
    print(
        f"🤖 AI Model: {config['provider']}/{config['model']} (from config.json)")

    # Check if input file exists
    if not os.path.exists(params['input_path']):
        print(f"❌ Input file not found: {params['input_path']}")
        return

    # Check if JSON file exists
    if not os.path.exists(params['json_inject_file']):
        print(f"❌ JSON file not found: {params['json_inject_file']}")
        return

    print("\n🧪 Performing dry run...")

    try:
        # Create injector instance
        injector = JSONInjector(param_file)

        # Perform dry run (for now, we'll just generate metadata without saving)
        print("Generating metadata...")
        metadata = injector._generate_metadata()
        result = {'success': True, 'metadata': metadata}

        if result['success']:
            print("✅ Dry run successful!")
            print(f"📋 Generated metadata:")
            for key, value in result['metadata'].items():
                print(f"   {key}: {value}")

            # Ask for confirmation
            print("\n" + "=" * 60)
            response = input(
                "🚀 Proceed with actual injection? (y/N): ").strip().lower()

            if response == 'y':
                print("\n🔄 Performing actual injection...")

                # Perform actual injection
                result = injector.inject()

                if result['success']:
                    print("✅ Metadata injection successful!")
                    # No backup files generated
                    print(f"📊 Updated JSON file: {params['json_inject_file']}")

                    # Show the updated entry
                    print(
                        f"\n📋 Updated entry for {params['target_filename']}:")
                    with open(params['json_inject_file'], 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    for file_entry in data['files']:
                        if file_entry['name'] == params['target_filename']:
                            print(json.dumps(file_entry,
                                  indent=2, ensure_ascii=False))
                            break
                else:
                    print(
                        f"❌ Injection failed: {result.get('error', 'Unknown error')}")
            else:
                print("⏹️  Injection cancelled by user.")
        else:
            print(f"❌ Dry run failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
