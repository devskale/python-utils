#!/usr/bin/env python3
"""
Simple script to inject metadata for a single file in the Lampen project.
"""

import os
import sys
import json

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
    """Inject metadata for the 191341-00.pdf file."""

    print("🔍 Injecting Metadata for 191341-00.pdf")
    print("=" * 50)

    param_file = "lampen_injection_params.json"

    try:
        # Create injector instance
        injector = JSONInjector(param_file)

        # Perform injection
        print("🔄 Performing metadata injection...")
        result = injector.inject()

        if result['success']:
            print("✅ Metadata injection successful!")
            # No backup files generated
            print(f"🎯 Target file: {result['target_file']}")

            # Show the injected metadata
            print(f"\n📋 Injected metadata:")
            for key, value in result['injected_metadata'].get('meta', {}).items():
                print(f"   {key}: {value}")

            # Show the updated entry
            print(f"\n📊 Updated entry in JSON file:")
            with open(injector.params['json_inject_file'], 'r', encoding='utf-8') as f:
                data = json.load(f)

            for file_entry in data['files']:
                if file_entry['name'] == injector.params['target_filename']:
                    print(json.dumps(file_entry, indent=2, ensure_ascii=False))
                    break
        else:
            print(
                f"❌ Injection failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error during injection: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
