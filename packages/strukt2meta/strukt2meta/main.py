import argparse
import json
import os
from strukt2meta.metadata_generator import generate_metadata
from strukt2meta.apicall import call_ai_model

# Replace the placeholder function
def query_ai_model(prompt, input_text, verbose=False):
    return call_ai_model(prompt, input_text, verbose)

def load_prompt(prompt_name):
    prompts_dir = "./prompts"
    prompt_path = os.path.join(prompts_dir, f"{prompt_name}.md")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, "r") as prompt_file:
        return prompt_file.read()

def main():
    parser = argparse.ArgumentParser(description="Process a strukt file and generate JSON metadata.")
    parser.add_argument("--i", "--inpath", required=False, default="./default_input.md", help="Path to the input markdown strukt file (default: ./default_input.md)")
    parser.add_argument("--p", "--prompt", default="zusammenfassung", help="Prompt file name (without .md) to use from the ./prompts directory (default: zusammenfassung)")
    parser.add_argument("--o", "--outfile", required=False, help="Path to the output JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode to stream API call response.")

    args = parser.parse_args()

    if args.o is None:
        parser.print_help()
        return

    # Read the input file
    with open(args.i, "r") as infile:
        input_text = infile.read()
        print(f"Input text loaded from: {args.i}")

    # Load the prompt
    prompt = load_prompt(args.p)
    print(f"Using prompt: {args.p}")

    # Query the AI model
    result = query_ai_model(prompt, input_text, verbose=args.verbose)

    # Write the result to the output file if not in verbose mode
    if not args.verbose:
        with open(args.o, "w") as outfile:
            json.dump(result, outfile, indent=4)
        print(f"Output written to: {args.o}")

if __name__ == "__main__":
    main()
