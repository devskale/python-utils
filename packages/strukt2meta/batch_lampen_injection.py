#!/usr/bin/env python3
"""
Batch metadata injection script for the Lampen (lighting) project.
This script processes all files in the directory and injects metadata.
"""

import os
import sys
import json
import glob
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


def get_file_mappings():
    """Get mappings between PDF/DOCX files and their markdown counterparts."""
    base_dir = ".disk/2025-04 Lampen/A"
    md_dir = os.path.join(base_dir, "md")

    # Get all original files (PDF and DOCX)
    original_files = []
    for ext in ["*.pdf", "*.docx", "*.xlsx"]:
        original_files.extend(glob.glob(os.path.join(base_dir, ext)))

    mappings = []

    for original_file in original_files:
        filename = os.path.basename(original_file)
        name_without_ext = os.path.splitext(filename)[0]

        # Look for corresponding markdown files
        md_files = glob.glob(os.path.join(md_dir, f"{name_without_ext}.*.md"))

        if md_files:
            # Prefer docling.md if available, otherwise take the first one
            preferred_md = None
            for md_file in md_files:
                if "docling.md" in md_file:
                    preferred_md = md_file
                    break

            if not preferred_md:
                preferred_md = md_files[0]

            mappings.append({
                'original_file': filename,
                'markdown_file': preferred_md,
                'relative_md_path': os.path.relpath(preferred_md, current_dir)
            })

    return mappings


def create_param_file(original_filename, md_path, temp_file="temp_injection_params.json"):
    """Create a temporary parameter file for a specific file."""
    params = {
        "input_path": md_path,
        "prompt": "lampen_metadata_extraction",
        "ai_model": "openai/gpt-4o-mini",
        "json_inject_file": ".disk/2025-04 Lampen/A/.pdf2md_index.json",
        "target_filename": original_filename,
        "injection_schema": {
            "meta": {
                "kategorie": {
                    "ai_generated_field": True,
                    "description": "Document category (e.g., Ausschreibung, Formblatt, Skizze, Vertrag)"
                },
                "name": {
                    "ai_generated_field": True,
                    "description": "Descriptive name of the document"
                },
                "document_type": {
                    "ai_generated_field": True,
                    "description": "Type of document (e.g., Bekanntmachung, Technische Spezifikation, Formular)"
                },
                "subject": {
                    "ai_generated_field": True,
                    "description": "Main subject or topic of the document"
                },
                "language": {
                    "ai_generated_field": True,
                    "description": "Document language (e.g., Deutsch, English)"
                }
            }
        },
        "backup_enabled": True,
        "validation_strict": False
    }

    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2, ensure_ascii=False)

    return temp_file


def main():
    """Process all files in the lighting project."""

    print("🔍 Batch Metadata Injection for Lampen Project")
    print("=" * 60)

    # Get file mappings
    mappings = get_file_mappings()

    if not mappings:
        print("❌ No file mappings found!")
        return

    print(f"📁 Found {len(mappings)} files to process")

    # Show preview
    print("\n📋 Files to process:")
    for i, mapping in enumerate(mappings[:5], 1):
        print(f"   {i}. {mapping['original_file']}")
    if len(mappings) > 5:
        print(f"   ... and {len(mappings) - 5} more files")

    # Ask for confirmation
    print("\n" + "=" * 60)
    response = input("🚀 Proceed with batch injection? (y/N): ").strip().lower()

    if response != 'y':
        print("⏹️  Batch injection cancelled by user.")
        return

    # Process files
    successful = 0
    failed = 0
    temp_param_file = "temp_injection_params.json"

    try:
        for i, mapping in enumerate(mappings, 1):
            print(
                f"\n🔄 Processing {i}/{len(mappings)}: {mapping['original_file']}")

            try:
                # Create temporary parameter file
                create_param_file(
                    mapping['original_file'], mapping['relative_md_path'], temp_param_file)

                # Create injector and process
                injector = JSONInjector(temp_param_file)
                result = injector.inject()

                if result['success']:
                    print(f"   ✅ Success: {mapping['original_file']}")
                    successful += 1
                else:
                    print(f"   ❌ Failed: {mapping['original_file']}")
                    failed += 1

            except Exception as e:
                print(
                    f"   ❌ Error processing {mapping['original_file']}: {str(e)}")
                failed += 1

    finally:
        # Clean up temporary file
        if os.path.exists(temp_param_file):
            os.remove(temp_param_file)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Batch Processing Summary:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📁 Total: {len(mappings)}")

    if successful > 0:
        print(f"\n💾 Updated JSON file: .disk/2025-04 Lampen/A/.pdf2md_index.json")
        print("🔍 You can now review the injected metadata in the JSON file.")


if __name__ == "__main__":
    main()
