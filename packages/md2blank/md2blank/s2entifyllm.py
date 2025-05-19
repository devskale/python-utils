import re
import os
import argparse
from providers_config import PROVIDER_CONFIGS
# Import uniinfer components and helpers
from uniinfer import (
    ChatMessage,
    ChatCompletionRequest,
    ProviderFactory
)
from credgoo import get_api_key
from dotenv import load_dotenv
import sys  # Import sys for exit
import time  # Import time module

# Load environment variables from .env file
dotenv_path = os.path.join(os.getcwd(), '.env')
found_dotenv = load_dotenv(dotenv_path=dotenv_path,
                           verbose=True, override=True)
if not found_dotenv:
    print(
        f"Warning: .env file not found at {dotenv_path}. Relying on existing environment variables.")

# --- Credential Handling ---
credgoo_encryption_token = os.getenv('CREDGOO_ENCRYPTION_KEY')
credgoo_api_token = os.getenv('CREDGOO_BEARER_TOKEN')

#if not credgoo_encryption_token or not credgoo_api_token:
#    print("Error: CREDGOO_ENCRYPTION_KEY or CREDGOO_BEARER_TOKEN not found in environment variables or .env file.")
#    print("Please ensure these variables are set.")
#    sys.exit(1)  # Exit if credentials are missing

# Define the target entities - expanded list
target_entities = "Personenname, Telefonnummer, E-Mail, Adressinformation, Firmenname"

# --- Prompts ---
prompt0 = """
Du bist ein intelligentes und hochpräzises(NER) Named Entity Recognizer System. Deine Aufgabe ist es die folgenden Entitätstypen im Text zu identifizieren: {target_entities}.
Diese Identifikation findet im Kontext der Prüfung von Ausschreibungsunterlagen und Angebotsunterlagen statt.
Gib jede gefundene Entität in einer neuen Zeile im Format 'Entitätstyp: Entitätswert' aus. Gib NUR die Entitäten aus, keine zusätzlichen Kommentare, Einleitungen oder den Originaltext. Außer den Entitäten antworte mit nichts.
Ignoriere generische oder allgemeine Begriffe wie 'Unternehmen' oder 'Projekte', 'IT-Dienstleistung'.

Text:
{text_chunk}

Identifizierte Entitäten:
"""

prompt1 = """
Du bist ein hochpräzises Named Entity Recognition (NER) System, spezialisiert auf die Analyse von Ausschreibungs- und Angebotsunterlagen. Deine Aufgabe ist es, ausschließlich die folgenden Entitätstypen zu erkennen und zu extrahieren: {target_entities}.

Extrahiere nur spezifische, identifizierbare Informationen (z. B. Eigennamen, IDs, Adressen). Allgemeine Begriffe wie Unternehmen, Bieter, Projekt usw. sind zu ignorieren, ebenso zu ignorieren sind Entitäten wie GISA, Manz oder Wiener Wohnen Hausbetreuung GmbH.

Gib jede gefundene Entität auf einer neuen Zeile im Format:
Entitätstyp: Entitätswert

Antwortformat strikt einhalten: Keine Kommentare, kein Fließtext, kein Originaltext – nur die extrahierten Entitäten.


Text:
{text_chunk}

Identifizierte Entitäten:
"""

prompt3 = """
Du bist ein hochpräzises Named Entity Recognition (NER) System, spezialisiert auf die Analyse von Ausschreibungs- und Angebotsunterlagen. Deine Aufgabe ist es, ausschließlich die folgenden Entitätstypen zu erkennen und zu extrahieren:

{target_entities}

Extrahiere ausschließlich **personenbezogene oder schützenswerte Informationen** im Kontext der Anbieter, z. B.:
- Namen, Kontakt- und Adressdaten
- Firmen mit persönlichem Bezug (z. B. Einzelunternehmer mit GmbH)
- Finanzinformationen wie IBAN, UID-Nummern oder Firmenbuchnummern, sofern sie zuordenbar sind

**Nicht extrahieren**:
- Leere oder nicht vorhandene Angaben
- Platzhalter wie „Musterstadt“, „Max Mustermann“ etc.
- Allgemeine Begriffe wie „Projekt“, „Unternehmen“, „Organisation“
- Namen öffentlicher Stellen oder bekannter Informationsanbieter wie **GISA**, **Manz**, **Wiener Wohnen Hausbetreuung GmbH**

**Wichtig**: Wenn im Text keine relevanten Entitäten gefunden werden, gib **keine Ausgabe zurück** – auch keine leeren Felder oder Listen. Gib **nur tatsächlich identifizierte Entitäten** aus.

Gib jede gefundene Entität auf einer neuen Zeile im folgenden Format aus:
`Entitätstyp: Entitätswert`

Antwortformat strikt einhalten: **Keine Kommentare, kein Fließtext, kein Originaltext – nur die extrahierten Entitäten.**

Text:
{text_chunk}

Identifizierte Entitäten:
"""

prompt4 = """
Du bist ein intelligentes und hochpräzises Named Entity Recognizer (NER) System. Deine Aufgabe ist es, im folgenden Text ausschließlich die folgenden Entitätstypen zu erkennen und zu extrahieren:

{target_entities}

Kontext: Ausschreibungsunterlagen und Angebotsunterlagen.

Gib jede gefundene Entität in einer neuen Zeile im Format:
Entitätstyp: Entitätswert

Wichtig:
– Gib **nur tatsächliche Werte** aus (keine leeren Felder oder Platzhalter wie 'Vorname:').
– Gib **nur relevante, personenbezogene oder schützenswerte Angaben** aus.
– Ignoriere allgemeine Begriffe wie „Unternehmen“ oder „Projekt“.
– Ignoriere bekannte öffentliche Namen wie GISA, Manz oder Wiener Wohnen Hausbetreuung GmbH – auch wenn sie eine GmbH enthalten.

Antwortformat streng einhalten: Keine Kommentare, kein Originaltext – nur die extrahierten Entitäten.

Beispiele:

Text:
Herr Mag. Johann Berger, wohnhaft in 1020 Wien, Untere Donaustraße 17/6, wurde mit der Erstellung des Gutachtens beauftragt. Ansprechpartnerin ist Frau DI Lisa Meier (Telefon: +43 1 123 4567, E-Mail: lisa.meier@example.com).

Identifizierte Entitäten:
Person: Johann Berger  
Adresse: Untere Donaustraße 17/6, 1020 Wien  
Person: Lisa Meier  
Telefonnummer: +43 1 123 4567  
E-Mail: lisa.meier@example.com

Text:
Die Unterlagen sind an Max Mustermann, c/o Planungsbüro Müller, Hauptstraße 12a, 8010 Graz, zu richten. Kontakt per E-Mail: max@planungsbuero.at oder telefonisch unter 0664 9876543.

Identifizierte Entitäten:
Person: Max Mustermann  
Adresse: Hauptstraße 12a, 8010 Graz  
E-Mail: max@planungsbuero.at  
Telefonnummer: 0664 9876543

Text:
{text_chunk}

Identifizierte Entitäten:
"""

prompt5 = """
Du bist ein hilfreiches Informationsextraktionssystem.

Aufgabe: Bei einem gegebenen Text besteht deine Aufgabe darin, spezifische persönliche Entitäten und Firmennamen zu extrahieren und ihre Entitätstypen zu identifizieren. Erfasse nur eindeutige, benannte Entitäten aus dem Text, die für die Identifikation von Personen oder Firmen relevant sind.
Extrahiere nur spezifische, identifizierbare Informationen aus folgenden Zielentitäten: {target_entities}

Beispiele für relevante Entitäten:

Konkrete Namen von Personen (z.B. "Maria Schmidt")
Spezifische Firmennamen (z.B. "Siemens AG", "Volkswagen")
Eindeutig benannte Orte (z.B. "Berlin", "Rhein")
Spezifische Datumsangaben, Zeitangaben, Geldbeträge

Allgemeine Begriffe und Beschreibungen wie "Innenstadt", "IT-Dienstleistungen" oder "Projekte" sollen NICHT als Entitäten erkannt werden, da es sich um Gattungsbegriffe handelt.
Die Ausgabe sollte in einer Liste von Tupeln im folgenden Format sein: [("Entität 1", "Typ der Entität 1"), ... ].

<TEXT>: 

{text_chunk}

</TEXT>: 

Identifizierte Entitäten:
"""


prompt_anonymizer0 = """
Du bist ein intelligentes Anonymisierungssystem. Deine Aufgabe ist es, aus dem folgenden Text personenbezogene oder schützenswerte Informationen zu erkennen und diese in strukturierter, anonymisierter Form darzustellen.

Kontext: Ausschreibungsunterlagen und Angebotsunterlagen.

Gib das Ergebnis ausschließlich im folgenden Format aus:

## GEWERBEBERECHTIGTE PERSON

**Bezeichnung:** [[Firmenname]]  
**Rechtsform:** Gesellschaft mit beschränkter Haftung  
**Firmenbuchnummer:** [[Firmenbuchnummer]]  
**Anschrift:** [[Adresse]]  
**GLN:** [[GLN]]

Wichtig:
– Erkenne relevante Angaben **aus dem Text** und setze diese in die vorgesehenen Felder ein.  
– Verwende `[[...]]` nur, wenn keine echte Information vorhanden oder erkennbar ist.  
– Ignoriere allgemeine Begriffe oder bekannte öffentliche Einrichtungen (z. B. GISA, Wiener Wohnen etc.).  
– Verwende keine Kommentare, keine Analyse – gib nur den strukturierten, anonymisierten Block zurück.  
– Beachte, dass nur reale, im Text genannte Angaben verwendet werden dürfen.

Text:
{text_chunk}

Anonymisierte Ausgabe:
"""


# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Extract entities from a chunked markdown file.")
parser.add_argument(
    "filename_base", help="The base name of the input file (e.g., 'ausschreibung' for 'ausschreibung.chunked.md')")
args = parser.parse_args()

# --- File Path Definitions ---
input_dir = "/Users/johannwaldherr/code/ww/ww_private/anonymizer/data"
# Construct filenames based on the provided base and schema
input_filename = f"{args.filename_base}.chunked.md"
output_filename = f"{args.filename_base}.entities.md"
input_filepath = os.path.join(input_dir, input_filename)
output_filepath = os.path.join(input_dir, output_filename)

# --- Uniinfer Provider Initialization ---
provider = "gemini"  # Hardcoded provider name
model = "gemini-2.0-flash"
# provider = "arli"  # Hardcoded provider name
# model = "Mistral-Nemo-12B-Instruct-2407"
selected_prompt = prompt0  # Default prompt

try:
    # Safely get extra_params using .get() for both levels
    provider_config = PROVIDER_CONFIGS.get(provider, {})
    extra_params = provider_config.get('extra_params', {})

    uni_provider = ProviderFactory().get_provider(
        name=provider,
        # Fetching API key via credgoo, assuming it's needed or ignored gracefully by uniinfer
        api_key=get_api_key(
            service=provider, encryption_key=credgoo_encryption_token, bearer_token=credgoo_api_token),
        **extra_params  # Pass the safely retrieved extra_params
    )
    print(f"Uniinfer provider initialized for {provider} ")
except KeyError as e:
    print(f"Error: Provider '{provider}' not found in PROVIDER_CONFIGS. {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error initializing Uniinfer provider: {e}")
    sys.exit(1)


# Function to call LLM for entity extraction from a text chunk using Uniinfer
def get_entities_from_text(chunk_data):
    """Processes a chunk of text through LLM and returns structured entity data."""
    text_chunk = chunk_data['text'] if isinstance(
        chunk_data, dict) else chunk_data
    formatted_prompt = selected_prompt.format(text_chunk=text_chunk,
                                              target_entities=target_entities)
    try:
        messages = [ChatMessage(role="user", content=formatted_prompt)]
        request = ChatCompletionRequest(
            messages=messages,
            model=model,  # Use the defined model
            streaming=True,

        )

        full_response = ""
        # Use the initialized uni_provider
        for chunk in uni_provider.stream_complete(request):
            if chunk.message and chunk.message.content:
                content = chunk.message.content
                full_response += content
        # Parse response into structured format
    entities = []
    for line in full_response.strip().split('\n'):
        if ':' in line:
            entity_type, entity_value = line.split(':', 1)
            entities.append({
                'type': entity_type.strip(),
                'value': entity_value.strip(),
                'chunk_metadata': chunk_data.get('metadata', {}) if isinstance(chunk_data, dict) else {},
                'chunk_number': chunk_data.get('metadata', {}).get('chunk_number', None) if isinstance(chunk_data, dict) else None,
                'source_filename': os.path.basename(input_filepath) if 'input_filepath' in globals() else None
            })
    return entities

    except Exception as e:
        print(f"Error calling LLM via Uniinfer for chunk: {e}")
        # Consider more specific error handling based on uniinfer exceptions if available
        return f"Error processing chunk: {e}"

# --- Main processing logic ---


# Read the input file
try:
    with open(input_filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"Successfully read input file: {input_filepath}")
except FileNotFoundError:
    print(f"Error: Input file not found at {input_filepath}")
    exit(1)
except Exception as e:
    print(f"Error reading input file: {e}")
    exit(1)

# Split content into chunks using regex (captures header and content separately)
# Pattern looks for '--- CHUNK X (Size: Y) ---' and captures it, splitting the text
chunk_pattern = r'(--- CHUNK \d+ \(Size: \d+\) ---)'
parts = re.split(chunk_pattern, content)
# Filter out empty strings and combine headers with their content
chunks = []
header = None
for part in parts:
    part = part.strip()
    if not part:
        continue
    if re.match(chunk_pattern, part):
        header = part
    elif header:
        chunks.append({"header": header, "content": part})
        header = None  # Reset header

print(f"Split input into {len(chunks)} chunks.")

# Open the output file in write mode (to clear previous content)
try:
    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        # Add filepath comment for consistency with user request format
        outfile.write(f"<!-- filepath: {output_filepath} -->\n")
        # Update header to reflect the dynamic input filename
        outfile.write(f"# Entities extracted from {input_filename}\n\n")
    print(f"Initialized output file: {output_filepath}")
except Exception as e:
    print(f"Error creating output file: {e}")
    exit(1)

# Process each chunk and collect entities
all_entities = []
processed_count = 0
for i, chunk_data in enumerate(chunks):
    chunk_header = chunk_data["header"]
    chunk_content = chunk_data["content"]

    print(f"Processing chunk {i+1}/{len(chunks)}: {chunk_header}")

    if not chunk_content:
        print("  Skipping empty chunk content.")
        continue

    # Get structured entities from chunk
    entities = get_entities_from_text({
        'text': chunk_content,
        'metadata': {
            'chunk_header': chunk_header,
            'chunk_number': i+1
        }
    })

    if entities:
        all_entities.extend(entities)
        print(f"  Found {len(entities)} entities in chunk {i+1}.")
    else:
        print("  No entities found in chunk.")

    # Add a 2-second pause after the request
    print("  Pausing for 2 seconds...")
    time.sleep(2)
    processed_count += 1

# Write all entities to output file in structured format
try:
    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(f"<!-- filepath: {output_filepath} -->\n")
        outfile.write(f"# Entities extracted from {input_filename}\n\n")
        outfile.write(f"Total entities found: {len(all_entities)}\n\n")

        for entity in all_entities:
            outfile.write(f"- {entity['type']}: {entity['value']}\n")
            outfile.write(
                f"  (From chunk {entity['chunk_metadata'].get('chunk_number', 'unknown')})\n\n")

    print(
        f"Successfully wrote {len(all_entities)} entities to {output_filepath}")
except Exception as e:
    print(f"Error writing to output file: {e}")

print(
    f"\nEntity extraction complete. Processed {processed_count}/{len(chunks)} chunks.")
print(f"Results saved to: {output_filepath}")
