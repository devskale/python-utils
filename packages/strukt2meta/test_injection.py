#!/usr/bin/env python3
"""
Test script for the JSON injection functionality.

This script demonstrates how to use the strukt2meta injection feature
to add AI-generated metadata to JSON files.
"""

from strukt2meta.injector import JSONInjector
import os
import sys
import json

# Add the strukt2meta package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'strukt2meta'))


def test_injection():
    """Test the injection functionality with sample data."""
    print("🧪 Testing strukt2meta JSON injection functionality")
    print("=" * 50)

    # Check if required files exist
    required_files = [
        "./injection_params_sample.json",
        "./sample_document.md",
        "./.pdf2md_index.json",
        "./prompts/metadata_extraction.md"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print("✅ All required files found")

    try:
        # Initialize injector
        print("\n📋 Loading injection parameters...")
        injector = JSONInjector("./injection_params_sample.json")

        print(f"   Target file: {injector.params['target_filename']}")
        print(f"   Input document: {injector.params['input_path']}")
        print(f"   Prompt: {injector.params['prompt']}")

        # Perform dry run first
        print("\n🔍 Performing dry run validation...")
        json_data = injector._load_target_json()
        target_entry = injector._find_target_file_entry(json_data)

        if target_entry:
            print(f"✅ Target file found in JSON")
            print(f"   Current meta: {target_entry.get('meta', 'None')}")
        else:
            print(f"❌ Target file not found in JSON")
            return False

        # Ask for confirmation
        response = input("\n❓ Proceed with actual injection? (y/N): ")
        if response.lower() != 'y':
            print("🚫 Injection cancelled by user")
            return True

        # Perform actual injection
        print("\n🚀 Executing injection...")
        result = injector.inject()

        if result['success']:
            print("✅ Injection completed successfully!")
            print(f"   Backup created: {result['backup_path']}")
            print("\n📊 Injected metadata:")
            print(json.dumps(result['injected_metadata'],
                  indent=2, ensure_ascii=False))
            return True
        else:
            print("❌ Injection failed")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False


if __name__ == "__main__":
    success = test_injection()
    sys.exit(0 if success else 1)
