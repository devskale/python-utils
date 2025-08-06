#!/usr/bin/env python3
"""
Example script showing how to use strukt2meta as an imported package.
"""

import json
from strukt2meta import query_ai_model, load_prompt


input_text = """
title: Betriebsversicherungsbestätigung
version: 1.0
date: 2025-04-22

---

# Allianz Versicherung AG

Betriebshaftpflichtversicherung
1010 Wien, Schottenring 35
Telefon: +43 1 878 00
E-Mail: wien@allianz.at

Wien, 22.04.2025

## Versicherungsbestätigung zur Vorlage bei Ausschreibung E

Betriebshaftpflichtversicherung mit Polizzennummer: AT123456789

Versicherungsnehmer: GrünTech GmbH
Wiener Straße 100, 1010 Wien

Versicherungssumme: € 5.000.000,- pro Schadensfall

Gültig bis: 31.12.2025

Diese Bestätigung dient als Nachweis für die Ausschreibung E (Lieferung von Aufsitzrasenmähern).

[Unterschrift]
Max Mustermann
Versicherungssachbearbeiter

"""


def main():
    """
    Example function demonstrating strukt2meta usage.
    """
    # Sample input text (could be from a file, API, etc.)

    try:
        # Load a prompt from the prompts directory
        prompt = load_prompt("bdok")
        print("✓ Prompt loaded successfully")

        # Process the text with AI model
        print("🤖 Processing with AI model...")
        result = query_ai_model(
            prompt=prompt,
            input_text=input_text,
            verbose=True,  # Set to True to see streaming output
            json_cleanup=True  # Enable JSON cleanup
        )

        # Display the result
        print("✓ Processing complete!")
        print("\n📄 Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # You can also save to file
        with open("output_example.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("💾 Result saved to output_example.json")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Make sure you're running this from the strukt2meta directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
