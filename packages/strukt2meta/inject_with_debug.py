#!/usr/bin/env python3
"""
Complete injection with debug output
"""

import os
import sys
import json

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from strukt2meta.injector import JSONInjector

def main():
    """Perform complete injection with debug output."""
    
    print("🔍 Complete Metadata Injection with Debug")
    print("=" * 60)
    
    try:
        # Create injector instance
        injector = JSONInjector("lampen_injection_params.json")
        
        print("📋 Parameters loaded successfully")
        
        # Perform the complete injection
        print("\n🚀 Starting injection process...")
        result = injector.inject()
        
        if result['success']:
            print("✅ Injection completed successfully!")
            print(f"💾 Backup created: {result.get('backup_path', 'N/A')}")
            
            # Show the injected metadata
            print("\n📊 Injected metadata:")
            print(json.dumps(result['injected_metadata'], indent=2, ensure_ascii=False))
            
            # Verify the injection by reading the JSON file
            print("\n🔍 Verifying injection in JSON file...")
            with open(injector.params['json_inject_file'], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find the target file entry
            target_filename = injector.params['target_filename']
            for file_entry in data['files']:
                if file_entry['name'] == target_filename:
                    print(f"📋 Found entry for {target_filename}:")
                    print(json.dumps(file_entry, indent=2, ensure_ascii=False))
                    
                    if 'meta' in file_entry and file_entry['meta']:
                        print("✅ Metadata successfully injected!")
                    else:
                        print("❌ Metadata field is empty!")
                    break
            else:
                print(f"❌ Target file {target_filename} not found in JSON!")
        else:
            print(f"❌ Injection failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()