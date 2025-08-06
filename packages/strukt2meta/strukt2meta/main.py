import argparse
import json
import os
from strukt2meta.apicall import call_ai_model

# Replace the placeholder function


def query_ai_model(prompt, input_text, verbose=False, json_cleanup=False):
    return call_ai_model(prompt, input_text, verbose, json_cleanup)


def load_prompt(prompt_name):
    prompts_dir = "./prompts"
    prompt_path = os.path.join(prompts_dir, f"{prompt_name}.md")
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, "r") as prompt_file:
        return prompt_file.read()


def main():
    parser = argparse.ArgumentParser(
        description="Process a strukt file and generate JSON metadata.")
    
    # Add subcommands for different operations
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command (original functionality)
    generate_parser = subparsers.add_parser('generate', help='Generate metadata from strukt file')
    generate_parser.add_argument("--i", "--inpath", required=False, default="./default_input.md",
                        help="Path to the input markdown strukt file (default: ./default_input.md)")
    generate_parser.add_argument("--p", "--prompt", default="zusammenfassung",
                        help="Prompt file name (without .md) to use from the ./prompts directory (default: zusammenfassung)")
    generate_parser.add_argument("--o", "--outfile", required=True,
                        help="Path to the output JSON file")
    generate_parser.add_argument("--j", "--json-cleanup", action="store_true",
                        help="Enable JSON cleanup to repair and clean AI-generated JSON output")
    generate_parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose mode to stream API call response.")
    
    # Inject command (new functionality)
    inject_parser = subparsers.add_parser('inject', help='Inject metadata into JSON file')
    inject_parser.add_argument("--params", "-p", required=True,
                        help="Path to the parameter configuration JSON file")
    inject_parser.add_argument("--dry-run", "-d", action="store_true",
                        help="Perform a dry run without actually modifying files")
    inject_parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return
    
    if args.command == 'generate':
        handle_generate_command(args)
    elif args.command == 'inject':
        handle_inject_command(args)


def handle_generate_command(args):
    """Handle the generate command (original functionality)."""
    # Read the input file
    with open(args.i, "r") as infile:
        input_text = infile.read()
        print(f"Input text loaded from: {args.i}")

    # Load the prompt
    prompt = load_prompt(args.p)
    print(f"Using prompt: {args.p}")

    # Query the AI model
    result = query_ai_model(prompt, input_text, verbose=args.verbose, json_cleanup=args.j)

    # Write the result to the output file
    with open(args.o, "w") as outfile:
        json.dump(result, outfile, indent=4)
        print(f"Output written to: {args.o}")


def handle_inject_command(args):
    """Handle the inject command (new functionality)."""
    from strukt2meta.injector import JSONInjector
    
    try:
        if args.verbose:
            print(f"Loading parameters from: {args.params}")
            
        injector = JSONInjector(args.params)
        
        if args.dry_run:
            print("DRY RUN MODE - No files will be modified")
            print("Parameter validation: PASSED")
            print(f"Target file: {injector.params['target_filename']}")
            print(f"JSON file: {injector.params['json_inject_file']}")
            print(f"Input path: {injector.params['input_path']}")
            print(f"Prompt: {injector.params['prompt']}")
            return
        
        # Execute injection
        result = injector.inject()
        
        if result['success']:
            print("✅ Injection completed successfully!")
            if args.verbose:
                print(f"Target file: {result['target_file']}")
                print(f"Backup created: {result['backup_path']}")
                print("Injected metadata:")
                print(json.dumps(result['injected_metadata'], indent=2, ensure_ascii=False))
        else:
            print("❌ Injection failed")
            
    except Exception as e:
        print(f"❌ Error during injection: {e}")
        raise


if __name__ == "__main__":
    main()
