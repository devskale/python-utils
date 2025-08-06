#!/usr/bin/env python3
"""
Test script for the new intelligent file discovery functionality.
This demonstrates the generalized strukt2meta capabilities.
"""

from strukt2meta.file_discovery import FileDiscovery
import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def test_file_discovery():
    """Test the file discovery functionality."""

    print("🧪 Testing File Discovery System")
    print("=" * 60)

    # Test with Lampen project directory
    test_directory = ".disk/2025-04 Lampen/A"

    if not os.path.exists(test_directory):
        print(f"❌ Test directory not found: {test_directory}")
        print("   Please run this test from the strukt2meta root directory")
        return

    # Initialize file discovery
    discovery = FileDiscovery(test_directory, "config.json")

    # Print discovery report
    discovery.print_discovery_report()

    # Test specific file lookup
    print("\n🔍 Testing specific file lookup:")
    test_file = "191341-00.pdf"
    best_md = discovery.get_best_markdown_for_file(test_file)

    if best_md:
        print(f"✅ Best markdown for {test_file}: {best_md}")
    else:
        print(f"❌ No markdown found for {test_file}")

    # Test metadata existence checking
    print("\n🏷️  Testing metadata existence checking:")
    json_file = os.path.join(test_directory, ".pdf2md_index.json")

    if os.path.exists(json_file):
        # Test with a file that has metadata
        meta_status = discovery.check_metadata_exists(
            "191341-00.pdf", json_file)
        print(f"✅ 191341-00.pdf metadata status: {meta_status}")

        # Test with a file that doesn't have metadata
        meta_status = discovery.check_metadata_exists(
            "2024_06001_Rahmenvertrag_EV.pdf", json_file)
        print(
            f"✅ 2024_06001_Rahmenvertrag_EV.pdf metadata status: {meta_status}")
    else:
        print(f"⚠️  JSON index file not found: {json_file}")

    # Test mappings
    print("\n📊 Testing file mappings:")
    mappings = discovery.discover_files()

    for mapping in mappings[:3]:  # Show first 3 mappings
        print(f"📄 {mapping.source_file} ({mapping.source_type})")
        print(f"   📝 Markdown files: {len(mapping.markdown_files)}")
        if mapping.best_markdown:
            print(f"   ⭐ Best: {mapping.best_markdown}")
            print(f"   🔧 Parser: {mapping.parser_used}")
            print(f"   📊 Confidence: {mapping.confidence_score:.2f}")
        print()


def test_cli_commands():
    """Test the new CLI commands."""

    print("\n🖥️  Testing CLI Commands")
    print("=" * 60)

    test_directory = ".disk/2025-04 Lampen/A"

    if not os.path.exists(test_directory):
        print(f"❌ Test directory not found: {test_directory}")
        return

    print("Available CLI commands to test:")
    print()
    print("1. Discover files:")
    print(f"   python -m strukt2meta.main discover -d '{test_directory}' -v")
    print()
    print("2. Analyze specific file:")
    print(
        f"   python -m strukt2meta.main analyze -d '{test_directory}' -f '191341-00.pdf' -p lampen_metadata_extraction")
    print()
    print("3. Analyze with metadata existence check:")
    print(
        f"   python -m strukt2meta.main analyze -d '{test_directory}' -f '191341-00.pdf' -p lampen_metadata_extraction -j '{test_directory}/.pdf2md_index.json' -v")
    print()
    print("4. Show available files for analysis:")
    print(f"   python -m strukt2meta.main analyze -d '{test_directory}'")
    print()
    print("5. Batch process (dry run):")
    print(
        f"   python -m strukt2meta.main batch -d '{test_directory}' -j '{test_directory}/.pdf2md_index.json' --dry-run")
    print()


if __name__ == "__main__":
    test_file_discovery()
    test_cli_commands()
