#!/usr/bin/env python3
"""
Example usage of the JSON to Excel/CSV converter

This script demonstrates how to use the json_to_excel_converter module
to convert document matching JSON files into structured Excel/CSV format.
"""

from json_to_excel_converter import convert_json_to_table
import os


def example_conversion():
    """
    Example function showing how to convert JSON files programmatically.
    """
    # Example JSON file path
    json_file = "matcha.Entrümpelung.Alpenglanz.json"

    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found!")
        return

    print("Converting JSON to Excel format...")
    try:
        # Convert to Excel
        excel_output = convert_json_to_table(json_file, 'xlsx')
        print(f"✓ Excel file created: {excel_output}")

        # Convert to CSV
        csv_output = convert_json_to_table(json_file, 'csv')
        print(f"✓ CSV file created: {csv_output}")

        print("\nConversion completed successfully!")
        print("\nFiles created:")
        print(f"  - {excel_output}")
        print(f"  - {csv_output}")

    except Exception as e:
        print(f"Error during conversion: {str(e)}")


if __name__ == '__main__':
    example_conversion()
