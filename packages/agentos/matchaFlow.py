"""
MatchaFlow Module

This module automates matching required documents to bidder uploads using LLM analysis.

Workflow:
1. Load required documents from audit or project data.
2. Load bidder's uploaded documents.
3. For each required document, use LLM to find matches based on metadata.
4. Save matches and update audit logs.

Dependencies:
- Python 3.8+
- OFS package for data access
- Agno framework for LLM integration
- Credgoo for API key management
- KontextBuilder for prompt generation
- Optional: json_repair for robust JSON parsing

Usage:
    python matchaFlow.py project@bidder [--limit N] [--id ID] [--verbose] [--test]
"""

import argparse
import json
import os
import re
import sys
import logging
from datetime import datetime

from ofs.api import list_bidder_docs_json, get_bieterdokumente_list, get_kriterien_audit_json  # type: ignore
from ofs.json_manager import update_json_file, update_audit_json

# from agno.tools import tool
# from agno.workflow.v2.workflow import Workflow
from kontextBuilder import kontextBuilder
from utils import extract_json_clean, create_agent




def findMatches(identifier, geforderte_dokumente, hochgeladene_docs, runner=1):
    return kontextBuilder(identifier, "matchgDok", geforderte_dokumente=geforderte_dokumente, hochgeladene_docs=hochgeladene_docs)


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
    """Main entry point for automated document matching.

    Parses command-line arguments, loads required and uploaded documents, matches them using LLM,
    and saves results to JSON files and audit logs.

    Command-line usage:
        python matchaFlow.py project@bidder [--limit N] [--id ID] [--verbose] [--test]
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
    parser.add_argument("--force", action="store_true",
                        help="Force re-matching of already matched documents")
    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING,
                            format='%(levelname)s: %(message)s')

    agent = create_agent()

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

    # Load audit for logging match events
    audit = get_kriterien_audit_json(project, bidder)

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

        # Check if matches already exist for this document
        bdok = next(
            (b for b in audit["bdoks"] if b["id"] == gefordertes_doc["id"]), None)
        if not args.force and bdok and "matches" in bdok:
            print(
                f"Skipping {gefordertes_doc['id']} - matches already exist")
            continue

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

            # Filter out invalid matches (e.g., null or empty Dateiname)
            if isinstance(matches, list):
                matches = [m for m in matches if isinstance(m, dict) and m.get("Dateiname") not in (None, "", "N/A")]

        # Add matches to the current required doc and to the aggregate list
        # gefordertes_doc["matches"] = matches  # Removed to avoid duplication
        matched_list.append({
            "gefordertes_doc": gefordertes_doc,
            "matches": matches,
        })

        # Log match event to audit.json verlauf
        if not args.test:
            if bdok:
                verlauf = bdok["audit"]["verlauf"]
                event = {
                    "zeit": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    "ereignis": "match",
                    "quelle_status": bdok["audit"].get("status"),
                    "ergebnis": f"Found {len(matches) if isinstance(matches, list) else 'N/A'} matches",
                    "akteur": "matchaFlow"
                }
                verlauf.append(event)
                # Add matches to the bdok
                bdok["matches"] = matches
                # Update audit status
                bdok["audit"]["zustand"] = "auditiert-ki"

    # Print the aggregated matched list for the processed items
    print("\nMatched list (first {} items):".format(limit or len(matched_list)))
    print(json.dumps(matched_list, indent=2, ensure_ascii=False))

    # Save match events to audit.json
    if not args.test:
        try:
            update_audit_json(project, bidder, "bdoks", audit["bdoks"])
            print("Updated audit.json with match events")
        except Exception as e:
            print(f"Error updating audit.json: {e}")

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
