#!/usr/bin/env python3
"""
Debug script to test metadata generation
"""

import os
import sys
import json

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from strukt2meta.injector import JSONInjector

def main():
    """Debug metadata generation."""
    
    print("🔍 Debug: Testing Metadata Generation")
    print("=" * 50)
    
    try:
        # Create injector instance
        injector = JSONInjector("lampen_injection_params.json")
        
        print("📋 Parameters loaded successfully")
        print(f"Input: {injector.params['input_path']}")
        print(f"Target: {injector.params['target_filename']}")
        
        # Test metadata generation
        print("\n🤖 Generating metadata...")
        metadata = injector._generate_metadata()
        
        print("✅ Metadata generated successfully!")
        print("📊 Generated metadata:")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        # Test validation
        print("\n🔍 Validating metadata...")
        is_valid = injector._validate_metadata(metadata)
        print(f"Validation result: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()