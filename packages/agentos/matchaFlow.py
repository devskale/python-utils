import argparse
import json
import os
import re
import sys
import logging
from credgoo import get_api_key
from ofs.api import list_bidder_docs_json, get_bieterdokumente_list, get_kriterien_audit_json  # type: ignore
# Agno framework pieces (used to construct the minimal workflow)
from agno.agent import Agent
from agno.models.vllm import VLLM
# from agno.tools import tool
# from agno.workflow.v2.workflow import Workflow
from kontextBuilder import kontextBuilder

# Optional JSON repair for messy LLM outputs
try:
    from json_repair import repair_json  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    repair_json = None  # type: ignore

 # ---------------- Environment / Model selection -----------------
PROVIDER = "tu"
BASE_URL = "https://aqueduct.ai.datalab.tuwien.ac.at/v1"
MODEL = "glm-4.5-355b"

api_key = get_api_key(PROVIDER)


def findMatches(identifier, geforderte_dokumente, hochgeladene_docs, runner=1):
    return kontextBuilder(identifier, "matchgDok", geforderte_dokumente=geforderte_dokumente, hochgeladene_docs=hochgeladene_docs)


def extract_json_clean(text: str):
    """Try to extract/parse JSON from a possibly noisy LLM response.

    Strategy:
    - Try direct json.loads
    - Try fenced code blocks ```json ... ``` or ``` ... ```
    - Try extracting just the matches array
    - Try using json_repair.repair_json when available
    Returns a Python object (dict or list) or None.
    """
    if not text:
        return None
    # 1) Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) Look for fenced json blocks
    for pattern in [r"```json\s*(.*?)```", r"```\s*(.*?)```"]:
        m = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if m:
            block = m.group(1).strip()
            try:
                return json.loads(block)
            except Exception:
                # Attempt repair on the block if available
                if repair_json:
                    try:
                        fixed = repair_json(block)
                        return json.loads(fixed)
                    except Exception:
                        pass
                continue

    # 3) Extract just the matches array and wrap it
    m2 = re.search(r'"matches"\s*:\s*(\[.*?\])', text, flags=re.DOTALL)
    if m2:
        arr_text = m2.group(1)
        try:
            matches = json.loads(arr_text)
            return {"matches": matches}
        except Exception:
            # Attempt repair on the array if available
            if repair_json:
                try:
                    fixed_arr = repair_json(arr_text)
                    matches = json.loads(fixed_arr)
                    return {"matches": matches}
                except Exception:
                    pass
            pass

    # 4) Last resort: try to repair the entire text
    if repair_json:
        try:
            fixed_all = repair_json(text)
            return json.loads(fixed_all)
        except Exception:
            pass

    return None


def get_bdoks_from_audit(project, bidder, specific_id=None):
    """
    Read the bdoks from audit.json for the given project and bidder,
    and transform them into the geforderte_dokumente format.

    Args:
        project (str): The project name
        bidder (str): The bidder name
        specific_id (str, optional): If provided, include this id even if prio <= 0

    Returns:
        list: List of geforderte dokumente with id, bezeichnung, kategorie, beschreibung, etc.
    """
    try:
        audit = get_kriterien_audit_json(project, bidder)
        bdoks = audit.get("bdoks", [])
    except Exception as e:
        print(f"Error reading audit.json for {project}@{bidder}: {e}")
        return []

    geforderte_dokumente = []
    for i, bdok in enumerate(bdoks):
        prio = bdok.get('prio')
        if prio is None:
            # Set default prio to 1 (in memory, not persisted)
            prio = 1

        if prio <= 0:
            # Skip documents with prio 0 or negative
            continue        # Transform bdok to gefordertes_doc format
        # bdok has 'id' and 'quelle' with the details
        gefordertes_doc = {
            'id': bdok.get('id'),
            'bezeichnung': bdok.get('quelle', {}).get('bezeichnung'),
            'kategorie': bdok.get('quelle', {}).get('kategorie'),
            'beschreibung': bdok.get('quelle', {}).get('beschreibung'),
            'fachliche_pruefung': bdok.get('quelle', {}).get('fachliche_pruefung'),
            # Include audit info if needed
            'status': bdok.get('audit', {}).get('status'),
            'prio': prio,
            'bewertung': bdok.get('audit', {}).get('bewertung'),
        }
        geforderte_dokumente.append(gefordertes_doc)

    return geforderte_dokumente


def main():
    """Minimal utility:

    - Accepts one positional argument in the form project@bidder
    - Calls ofs.api.list_bidder_docs_json(project, bidder)
    - Prints the returned JSON nicely
    """
    parser = argparse.ArgumentParser(
        description="List bidder docs JSON for project@bidder")
    parser.add_argument("identifier", help="project@bidder")
    parser.add_argument("--limit", type=int, default=100,
                        help="Number of required docs to process (default: 100)")
    parser.add_argument(
        "--id", help="Specific required document ID to check (optional)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output for debugging")
    parser.add_argument("--test", action="store_true",
                        help="Test mode: build prompts but skip LLM calls")
    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING,
                            format='%(levelname)s: %(message)s')

    agent = Agent(
        model=VLLM(
            base_url=BASE_URL,
            api_key=api_key,
            id=MODEL,
            max_retries=3,
            # stream=True,
        ),
        tools=[],
    )

    identifier = args.identifier
    if "@" not in identifier:
        print("Expected identifier in the form project@bidder")
        sys.exit(2)
    project, bidder = identifier.split("@", 1)

    try:
        hochgeladene_dokumente = list_bidder_docs_json(
            project, bidder, include_metadata=False)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # geforderte_dokumente = get_bieterdokumente_list(project)
    geforderte_dokumente = get_bdoks_from_audit(project, bidder, args.id)
    if not geforderte_dokumente:
        # Fallback to projekt.json if audit bdoks is empty
        geforderte_dokumente = get_bieterdokumente_list(project)
    assert geforderte_dokumente, f"No geforderte dokumente found for project {project}"
    print(f"gDoks: {len(geforderte_dokumente)}")
    print(f"bDoks: {len(hochgeladene_dokumente['documents'])}")

    if args.id:
        geforderte_dokumente = [
            d for d in geforderte_dokumente if d.get('id') == args.id]
        if not geforderte_dokumente:
            print(
                f"Document {args.id} has prio <= 0 or not found, skipping analysis")
            sys.exit(0)
        print("Das geforderte Dokument ist:")
        print(json.dumps(
            geforderte_dokumente[0], indent=2, ensure_ascii=False))
    # print(json.dumps(hochgeladene_dokumente, indent=2, ensure_ascii=False))
    # print(json.dumps(geforderte_dokumente, indent=2, ensure_ascii=False))
    # Build a matched list for the first N required docs
    limit = max(0, int(args.limit))
    matched_list = []

    # loop through geforderte_dokumente and print index and bezeichnung
    for i, gefordertes_doc in enumerate(geforderte_dokumente, start=1):
        if limit and i > limit:
            break
        logging.info(
            f"{i}/{len(geforderte_dokumente)} - {gefordertes_doc.get('bezeichnung')}")
        # ask llm if bieterdoc matches a gefordertes_doc
        # if yes, print match, if no, print no match
        mPrompt = findMatches(identifier,
                              gefordertes_doc, hochgeladene_dokumente, i)
        # Show only the first 100 characters of the prompt for preview
        preview = mPrompt[:100].replace("\n", " ")
        if len(mPrompt) > 100:
            preview += "..."
        logging.info(f"Prompt preview: {preview}")
        logging.info(f"gDok: {str(gefordertes_doc)[:100]}...")
        logging.info(
            f"hDok: {str(hochgeladene_dokumente['documents'])[:400]}...")

        if args.test:
            # Test mode: skip LLM call
            logging.info("Test mode: skipping LLM call")
            matches = []
        else:
            response = agent.run(
                mPrompt,
                stream=False,  # capture final text only
                markdown=False,
                show_message=False
            )
            # Parse the response into JSON (clean) and attach to current required doc
            content = getattr(response, "content", response)
            result = extract_json_clean(
                content if isinstance(content, str) else str(content))
            matches = None
            if isinstance(result, dict) and "matches" in result:
                matches = result["matches"]
            elif isinstance(result, list):
                matches = result
            else:
                logging.warning(
                    "Could not extract matches JSON cleanly; storing raw content.")
                matches = content

        # Add matches to the current required doc and to the aggregate list
        # gefordertes_doc["matches"] = matches  # Removed to avoid duplication
        matched_list.append({
            "gefordertes_doc": gefordertes_doc,
            "matches": matches,
        })

    # Print the aggregated matched list for the processed items
    print("\nMatched list (first {} items):".format(limit or len(matched_list)))
    print(json.dumps(matched_list, indent=2, ensure_ascii=False))

    # Save matched list to file
    os.makedirs("logs", exist_ok=True)
    out_file = f"logs/matcha.{project}.{bidder}.json"
    try:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(matched_list, f, indent=2, ensure_ascii=False)
        print(f"Saved matched list to {out_file}")
    except Exception as e:
        print(f"Error saving matched list to {out_file}: {e}")


if __name__ == "__main__":
    main()
