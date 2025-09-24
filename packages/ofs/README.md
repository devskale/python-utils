# OFS (Opinionated Filesystem)

A Python package for managing opinionated filesystem structures designed to organize tender documents (Ausschreibungsdokumente) and bidder documents (Bieterdokumente) in a standardized, efficient manner.

## Installation

```bash
# Install from source
cd /path/to/ofs
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Navigate to your OFS directory
cd /path/to/your/.dir

# List all projects
ofs list-projects

# List bidders in a project
ofs list-bidders "ProjectName"

# View project structure
ofs tree

# Analyze criteria for a project
ofs projekt "ProjectName" pop

# Sync criteria across all projects and bidders
ofs projekt-sync
```

## Configuration

OFS uses a hierarchical configuration system:

1. **Environment variables** (highest priority)
2. **Local config**: `ofs.config.json` in current directory
3. **User config**: `~/.ofs/config.json`
4. **Defaults** (lowest priority)

### Basic Configuration

```json
{
  "BASE_DIR": ".dir",
  "INDEX_FILE": ".ofs.index.json",
  "METADATA_SUFFIX": ".meta.json"
}
```

### Environment Variables

```bash
export OFS_BASE_DIR="/path/to/documents"
export OFS_INDEX_FILE=".custom.index.json"
```

## CLI Usage

### Core Commands

```bash
# Path resolution
ofs get-path "ProjectName"           # Find project or bidder
ofs root                             # Show OFS root directory

# Project management
ofs list-projects                    # List all projects
ofs list-bidders "ProjectName"       # List bidders in project
ofs find-bidder "Project" "Bidder"   # Find specific bidder

# Document operations
ofs list-docs "ProjectName"          # List project documents
ofs list-docs "Project@Bidder"       # List bidder documents
ofs read-doc "Project@Bidder@doc.pdf" # Read document content

# Structure visualization
ofs tree                             # Show directory tree
ofs tree -d                          # Show directories only
```

### JSON Data Management

OFS provides powerful CLI commands for reading and writing JSON data in `projekt.json` and `audit.json` files:

#### Reading JSON Data

```bash
# Read entire projekt.json
ofs json read "ProjectName" projekt.json

# Read specific nested keys
ofs json read "ProjectName" projekt.json meta.schema_version
ofs json read "ProjectName" projekt.json meta.meta.auftraggeber

# Read array elements
ofs json read "ProjectName" projekt.json meta.meta.lose.0.nummer

# Read entire audit.json for a bidder
ofs json read "ProjectName" audit.json --bidder "BidderName"

# Read specific keys from audit.json
ofs json read "ProjectName" audit.json meta.bieter --bidder "BidderName"
ofs json read "ProjectName" audit.json kriterien.0.id --bidder "BidderName"
```

#### Writing JSON Data

```bash
# Update existing values in projekt.json
ofs json update "ProjectName" projekt.json meta.schema_version "3.4-updated"

# Create new nested structures
ofs json update "ProjectName" projekt.json new.nested.key "value"

# Update array elements
ofs json update "ProjectName" projekt.json meta.meta.lose.0.nummer "Updated Los"

# Update audit.json for specific bidder
ofs json update "ProjectName" audit.json meta.bieter "NewBidderName" --bidder "OldBidderName"

# Update without creating backup
ofs json update "ProjectName" projekt.json meta.version "1.0" --no-backup
```

#### JSON Command Examples

```bash
# Example: Update project schema version
ofs json update "Samples" projekt.json meta.schema_version "3.4-production"

# Example: Read contractor information
ofs json read "Samples" projekt.json meta.meta.auftraggeber
# Output: "Wiener Wohnen Hausbetreuung GmbH"

# Example: Update bidder name in audit
ofs json update "Samples" audit.json meta.bieter "Updated Bidder Ltd" --bidder "SampleBieter"

# Example: Read first criterion ID
ofs json read "Samples" audit.json kriterien.0.id --bidder "SampleBieter"
# Output: "F_FORM_001"

# Example: Create complex nested data
ofs json update "Samples" projekt.json api_config '{"version": "1.0", "features": ["read", "write"]}'
```

### Criteria Management

```bash
# Analyze criteria
ofs projekt "Project" pop          # Show next unproven criteria
ofs projekt "Project" tree         # Show criteria hierarchy
ofs projekt "Project" tag "ID"     # Show specific criterion

# Sync criteria to bidder audits
ofs projekt-sync                   # Sync all projects/bidders
ofs projekt-sync "Project"         # Sync all bidders in project
ofs projekt-sync "Project" "Bidder" # Sync specific bidder

Nach dem Sync enthält jede `audit.json` jetzt zusätzlich zum Abschnitt `kriterien` auch einen Abschnitt `bdoks` (Bieter-Dokumentenanforderungen) aus `projekt.json` (`bdoks.bieterdokumente`). Die Synchronisation ist idempotent: unveränderte Dokumentanforderungen erzeugen keine zusätzlichen Events. Entfernte Dokumentanforderungen werden mit `status: "entfernt"` markiert und erhalten ein einmaliges `entfernt`-Event.

# Record audit events
ofs kriterien-audit ki "Project" "Bidder" "CRITERION_ID"
ofs kriterien-audit mensch "Project" "Bidder" "CRITERION_ID"
ofs kriterien-audit freigabe "Project" "Bidder" "CRITERION_ID"
ofs kriterien-audit ablehnung "Project" "Bidder" "CRITERION_ID"
```

### Index Management

```bash
ofs index create "/path"             # Create index
ofs index update "/path"             # Update existing index
ofs index clear "/path"              # Remove index files
ofs index stats "/path"              # Show index statistics
```

## Python API

### Basic Operations

```python
import ofs

# Basic operations
path = ofs.get_path("ProjectName")
projects = ofs.list_projects()
bidders = ofs.list_bidders("ProjectName")

# Document management
docs = ofs.list_project_docs_json("ProjectName")
content = ofs.read_doc("Project@Bidder@document.pdf")

# Tree structure
tree = ofs.generate_tree_structure()
print(ofs.print_tree_structure())
```

### JSON Data Management

OFS provides a comprehensive Python API for reading and writing JSON data:

#### Reading JSON Data

```python
from ofs.core import read_json_file, read_audit_json

# Read entire projekt.json
project_data = read_json_file("ProjectName", "projekt.json")
print(f"Schema version: {project_data['meta']['schema_version']}")

# Read specific nested keys
schema_version = read_json_file("ProjectName", "projekt.json", "meta.schema_version")
auftraggeber = read_json_file("ProjectName", "projekt.json", "meta.meta.auftraggeber")

# Read array elements
first_los = read_json_file("ProjectName", "projekt.json", "meta.meta.lose.0.nummer")

# Read entire audit.json for a bidder
audit_data = read_audit_json("ProjectName", "BidderName")
print(f"Bidder: {audit_data['meta']['bieter']}")

# Read specific keys from audit.json
bieter_name = read_audit_json("ProjectName", "BidderName", "meta.bieter")
kriterien = read_audit_json("ProjectName", "BidderName", "kriterien")
```

#### Writing JSON Data

```python
from ofs.core import update_json_file, update_audit_json

# Update existing values in projekt.json
result = update_json_file("ProjectName", "projekt.json", "meta.schema_version", "3.4-updated")

# Create new nested structures
complex_data = {
    "api_config": {
        "version": "1.0",
        "features": ["read", "write", "nested_access"],
        "settings": {
            "backup": True,
            "atomic_writes": True
        }
    }
}
result = update_json_file("ProjectName", "projekt.json", "config", complex_data)

# Update array elements
result = update_json_file("ProjectName", "projekt.json", "meta.meta.lose.0.nummer", "Updated Los")

# Update audit.json for specific bidder
result = update_audit_json("ProjectName", "BidderName", "meta.bieter", "New Bidder Name")

# Update without creating backup
result = update_json_file("ProjectName", "projekt.json", "meta.version", "1.0", create_backup=False)
```

#### Complete Example: Project Analysis

```python
from ofs.core import read_json_file, read_audit_json, update_audit_json
import json

def analyze_project(project_name):
    """Comprehensive project analysis example"""
    
    # Read project metadata
    project_data = read_json_file(project_name, "projekt.json")
    
    print(f"=== Project Analysis: {project_name} ===")
    print(f"Schema Version: {project_data['meta']['schema_version']}")
    print(f"Auftraggeber: {project_data['meta']['meta']['auftraggeber']}")
    print(f"Aktenzeichen: {project_data['meta']['meta']['aktenzeichen']}")
    
    # Analyze Lose (lots)
    lose = read_json_file(project_name, "projekt.json", "meta.meta.lose")
    print(f"\nLose ({len(lose)} total):")
    for i, los in enumerate(lose):
        print(f"  {i+1}. {los['nummer']}: {los['bezeichnung']}")
    
    # Get bidders list (you would implement this based on your directory structure)
    # bidders = ofs.list_bidders(project_name)
    
    return project_data

def audit_bidder_criteria(project_name, bidder_name):
    """Example of bidder criteria auditing"""
    
    # Read bidder audit data
    audit_data = read_audit_json(project_name, bidder_name)
    
    print(f"=== Bidder Audit: {bidder_name} ===")
    print(f"Bieter: {audit_data['meta']['bieter']}")
    print(f"Projekt: {audit_data['meta']['projekt']}")
    
    # Analyze criteria
    kriterien = audit_data.get('kriterien', [])
    print(f"\nKriterien ({len(kriterien)} total):")
    
    status_counts = {}
    for kriterium in kriterien:
        status = kriterium.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"  {kriterium['id']}: {status}")
        
        # Show audit trail
        verlauf = kriterium.get('audit', {}).get('verlauf', [])
        if verlauf:
            latest = verlauf[-1]
            print(f"    Latest: {latest['ereignis']} by {latest['akteur']} at {latest['zeit']}")
    
    print(f"\nStatus Summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    return audit_data

def update_project_metadata(project_name, updates):
    """Example of updating project metadata"""
    
    print(f"=== Updating Project Metadata: {project_name} ===")
    
    for key_path, value in updates.items():
        try:
            result = update_json_file(project_name, "projekt.json", key_path, value)
            if result:
                print(f"✓ Updated {key_path} = {value}")
            else:
                print(f"✗ Failed to update {key_path}")
        except Exception as e:
            print(f"✗ Error updating {key_path}: {e}")

# Usage examples
if __name__ == "__main__":
    # Analyze a project
    project_data = analyze_project("Samples")
    
    # Audit a bidder
    audit_data = audit_bidder_criteria("Samples", "SampleBieter")
    
    # Update project metadata
    updates = {
        "meta.schema_version": "3.4-api-updated",
        "api_metadata.last_updated": "2025-09-24T12:00:00Z",
        "api_metadata.updated_by": "Python API"
    }
    update_project_metadata("Samples", updates)
```

#### Error Handling

```python
from ofs.core import read_json_file, update_json_file

def safe_json_operations(project_name):
    """Example of proper error handling"""
    
    try:
        # Attempt to read data
        data = read_json_file(project_name, "projekt.json", "meta.schema_version")
        print(f"Current schema version: {data}")
        
    except FileNotFoundError as e:
        print(f"Project or file not found: {e}")
        
    except KeyError as e:
        print(f"Key not found in JSON: {e}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    try:
        # Attempt to update data
        result = update_json_file(project_name, "projekt.json", "meta.last_check", "2025-09-24")
        if result:
            print("Update successful")
        else:
            print("Update failed")
            
    except Exception as e:
        print(f"Update error: {e}")

# Test error handling
safe_json_operations("NonExistentProject")  # Will show proper error handling
```

### Criteria Management

```python
# Criteria management
criteria = ofs.load_kriterien("/path/to/kriterien.json")
unproven = ofs.get_unproven_kriterien(criteria)
```

## Practical Usage Examples

### Common Workflows

#### 1. Project Setup and Initial Analysis

```bash
# Navigate to your OFS directory
cd /path/to/your/.dir

# List all available projects
ofs list-projects

# Analyze a specific project
ofs json read "ProjectName" projekt.json meta.meta.auftraggeber
ofs json read "ProjectName" projekt.json meta.meta.lose

# Check project schema version
ofs json read "ProjectName" projekt.json meta.schema_version
```

#### 2. Bidder Management Workflow

```bash
# List all bidders in a project
ofs list-bidders "ProjectName"

# Read bidder information
ofs json read "ProjectName" audit.json meta.bieter --bidder "BidderName"

# Check bidder criteria status
ofs json read "ProjectName" audit.json kriterien --bidder "BidderName"

# Update bidder information
ofs json update "ProjectName" audit.json meta.bieter "Updated Bidder Name" --bidder "BidderName"
```

#### 3. Criteria Synchronization and Auditing

```bash
# Sync criteria from projekt.json to all bidder audit.json files
ofs projekt-sync "ProjectName"

# Sync specific bidder
ofs projekt-sync "ProjectName" "BidderName"

# Record audit events
ofs kriterien-audit ki "ProjectName" "BidderName" "CRITERION_ID"
ofs kriterien-audit freigabe "ProjectName" "BidderName" "CRITERION_ID"
```

#### 4. Data Backup and Recovery

```bash
# All updates create automatic backups by default
ofs json update "ProjectName" projekt.json meta.schema_version "3.4-updated"

# Check backup files
ls -la .dir/ProjectName/projekt.json.backup.*

# Update without backup (use carefully)
ofs json update "ProjectName" projekt.json temp.data "test" --no-backup
```

### Python Integration Examples

#### 1. Automated Project Analysis Script

```python
#!/usr/bin/env python3
"""
Automated OFS project analysis script
"""

from ofs.core import read_json_file, read_audit_json
import sys

def analyze_all_projects():
    """Analyze all projects in the OFS directory"""
    
    # You would implement list_projects() based on your directory structure
    projects = ["Samples"]  # Replace with actual project discovery
    
    for project in projects:
        try:
            print(f"\n{'='*50}")
            print(f"PROJECT: {project}")
            print(f"{'='*50}")
            
            # Read project metadata
            project_data = read_json_file(project, "projekt.json")
            meta = project_data.get('meta', {}).get('meta', {})
            
            print(f"Auftraggeber: {meta.get('auftraggeber', 'N/A')}")
            print(f"Aktenzeichen: {meta.get('aktenzeichen', 'N/A')}")
            print(f"Ausschreibungsgegenstand: {meta.get('ausschreibungsgegenstand', 'N/A')}")
            
            # Analyze Lose
            lose = meta.get('lose', [])
            print(f"\nLose ({len(lose)} total):")
            for los in lose:
                print(f"  - {los.get('nummer', 'N/A')}: {los.get('bezeichnung', 'N/A')}")
            
        except Exception as e:
            print(f"Error analyzing project {project}: {e}")

if __name__ == "__main__":
    analyze_all_projects()
```

#### 2. Bidder Audit Report Generator

```python
#!/usr/bin/env python3
"""
Generate comprehensive bidder audit reports
"""

from ofs.core import read_audit_json
from datetime import datetime
import json

def generate_audit_report(project_name, bidder_name):
    """Generate a comprehensive audit report for a bidder"""
    
    try:
        audit_data = read_audit_json(project_name, bidder_name)
        
        print(f"AUDIT REPORT")
        print(f"Generated: {datetime.now().isoformat()}")
        print(f"Project: {project_name}")
        print(f"Bidder: {bidder_name}")
        print("="*60)
        
        # Meta information
        meta = audit_data.get('meta', {})
        print(f"\nMETA INFORMATION:")
        print(f"  Schema Version: {meta.get('schema_version', 'N/A')}")
        print(f"  Projekt: {meta.get('projekt', 'N/A')}")
        print(f"  Bieter: {meta.get('bieter', 'N/A')}")
        
        # Criteria analysis
        kriterien = audit_data.get('kriterien', [])
        print(f"\nCRITERIA ANALYSIS ({len(kriterien)} total):")
        
        status_summary = {}
        for kriterium in kriterien:
            status = kriterium.get('status', 'unknown')
            status_summary[status] = status_summary.get(status, 0) + 1
            
            print(f"\n  Criterion: {kriterium.get('id', 'N/A')}")
            print(f"    Status: {status}")
            
            # Audit trail
            audit = kriterium.get('audit', {})
            verlauf = audit.get('verlauf', [])
            
            if verlauf:
                print(f"    Audit Trail ({len(verlauf)} events):")
                for event in verlauf[-3:]:  # Show last 3 events
                    print(f"      {event.get('zeit', 'N/A')}: {event.get('ereignis', 'N/A')} by {event.get('akteur', 'N/A')}")
        
        print(f"\nSTATUS SUMMARY:")
        for status, count in status_summary.items():
            print(f"  {status}: {count}")
        
        return audit_data
        
    except Exception as e:
        print(f"Error generating audit report: {e}")
        return None

# Usage
if __name__ == "__main__":
    generate_audit_report("Samples", "SampleBieter")
```

#### 3. Bulk Data Operations

```python
#!/usr/bin/env python3
"""
Bulk operations for OFS data management
"""

from ofs.core import read_json_file, update_json_file, read_audit_json, update_audit_json

def bulk_update_schema_versions(projects, new_version):
    """Update schema version across multiple projects"""
    
    results = {}
    
    for project in projects:
        try:
            # Read current version
            current_version = read_json_file(project, "projekt.json", "meta.schema_version")
            print(f"Project {project}: {current_version} -> {new_version}")
            
            # Update to new version
            result = update_json_file(project, "projekt.json", "meta.schema_version", new_version)
            results[project] = "success" if result else "failed"
            
        except Exception as e:
            print(f"Error updating {project}: {e}")
            results[project] = f"error: {e}"
    
    return results

def validate_project_integrity(project_name):
    """Validate project data integrity"""
    
    issues = []
    
    try:
        # Check projekt.json
        project_data = read_json_file(project_name, "projekt.json")
        
        # Validate required fields
        required_fields = [
            "meta.schema_version",
            "meta.meta.auftraggeber",
            "meta.meta.aktenzeichen"
        ]
        
        for field in required_fields:
            try:
                value = read_json_file(project_name, "projekt.json", field)
                if not value:
                    issues.append(f"Empty required field: {field}")
            except:
                issues.append(f"Missing required field: {field}")
        
        # Check for bidders (you would implement bidder discovery)
        # bidders = list_bidders(project_name)
        # for bidder in bidders:
        #     try:
        #         audit_data = read_audit_json(project_name, bidder)
        #         # Validate audit data
        #     except Exception as e:
        #         issues.append(f"Bidder {bidder} audit error: {e}")
        
    except Exception as e:
        issues.append(f"Project data error: {e}")
    
    return issues

# Usage examples
if __name__ == "__main__":
    # Bulk update example
    projects = ["Samples"]  # Replace with actual project list
    results = bulk_update_schema_versions(projects, "3.4-bulk-updated")
    print("Bulk update results:", results)
    
    # Integrity check example
    issues = validate_project_integrity("Samples")
    if issues:
        print("Integrity issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Project integrity check passed")
```

## OFS Structure

OFS organizes documents in a specific directory structure:

```
.dir/                                    # BASE_DIR
├── .ofs.index.json                    # Project index
├── ProjectName/                       # Project folder
│   ├── .ofs.index.json               # Project index
│   ├── A/                            # Tender documents
│   │   ├── .ofs.index.json
│   │   ├── document.pdf
│   │   └── md/                       # Processed versions
│   │       └── document.docling.md
│   ├── B/                            # Bidder documents
│   │   ├── BidderName/
│   │   │   ├── .ofs.index.json
│   │   │   ├── bid.pdf
│   │   │   └── md/
│   │   └── audit.json               # Bieter audit
│   └── projekt.json                 # Projekt Info
└── archive/                          # Archived projects
```

### Reserved Directories

- **A/**: Tender documents (Ausschreibungsdokumente)
- **B/**: Bidder documents (Bieterdokumente)
- **md/**: Processed document versions
- **archive/**: Archived content

## Key Concepts

### Document Types

- **Ausschreibungsdokumente**: Tender documents from contracting authorities
- **Bieterdokumente**: Bid documents submitted by bidders
- **Index Files**: `.ofs.index.json` files tracking document metadata
- **Metadata Files**: JSON files with project and document information

### Criteria System

OFS includes a comprehensive criteria evaluation system:

- **kriterien.json**: Defines evaluation criteria for tenders
- **audit.json**: Tracks review status for each bidder's criteria
- **Audit Events**: Record KI reviews, human reviews, approvals, and rejections

### Supported File Types

- PDF (text-based or scanned)
- Office documents (docx, xlsx, pptx)
- Text files (txt)
- Images (jpg, jpeg, png)

## Metadata Files

### projekt.json

**Location**: `PROJEKTNAME/projekt.json`

Das projekt.json File enthält umfassendes Know-how über das Projekt und wird teilweise durch LLM generiert. Es beinhaltet:

- **Meta-Informationen**: Schema-Version, Auftraggeber, Aktenzeichen, Ausschreibungsgegenstand
- **Projekt-Details**: Datum, Lose-Beschreibungen, Bewertungsprinzipien
- **Bieter-Dokumentenanforderungen (bdoks)**: Vollständige Liste aller erforderlichen Dokumente mit:
  - Anforderungstyp (Pflichtdokument, Bedarfsfall)
  - Dokumenttyp (Angebot, Formblatt, Nachweis, Zusatzdokument)
  - Bezeichnung und Beschreibung
  - Unterzeichnungsanforderungen
  - Gültigkeitsdauer
- **Kriterien-IDs**: Strukturierte Auflistung aller Bewertungskriterien (Formal, Eignung, Zuschlag)

Beispiel-Struktur:

```json
{
  "meta": {
    "schema_version": "3.3-ai-optimized",
    "meta": {
      "auftraggeber": "Wiener Wohnen Hausbetreuung GmbH",
      "aktenzeichen": "2022_10001_AAB_EV",
      "ausschreibungsgegenstand": "Beschaffung von Reinigungsmaterialien"
    }
  },
  "bdoks": {
    "bieterdokumente": [...]
  },
  "ids": {
    "kriterien": [...]
  }
}
```

### audit.json

**Location**: `PROJEKTNAME/B/BIETERNAME/audit.json`

Das audit.json File beinhaltet die Bieter-Audit-Informationen und dokumentiert den kompletten Bewertungsprozess für jeden Bieter. Es enthält:

- **Meta-Informationen**: Schema-Version, Projekt- und Bieter-Bezeichnung
- **Kriterien-Audit**: Für jedes Bewertungskriterium:
  - Status (z.B. "entfernt", "geprüft", "freigegeben")
  - Priorität und Bewertung
  - Vollständiger Audit-Trail mit Zeitstempel
  - Ereignis-Historie (kopiert, entfernt, geprüft, etc.)
  - Akteur-Information (system, KI, Mensch)
- **Bieter-Dokumentenanforderungen (bdoks)**: Synchronisiert aus projekt.json
- **Audit-Verlauf**: Chronologische Dokumentation aller Änderungen

Beispiel-Struktur:

```json
{
  "meta": {
    "schema_version": "1.0-bieter-kriterien",
    "projekt": "2025-04 Lampen",
    "bieter": "Lampion GmbH"
  },
  "kriterien": [
    {
      "id": "E_BERUFL_001",
      "status": "entfernt",
      "audit": {
        "zustand": "synchronisiert",
        "verlauf": [
          {
            "zeit": "2025-08-21T14:24:55.124360Z",
            "ereignis": "kopiert",
            "akteur": "system"
          }
        ]
      }
    }
  ]
}
```

### kriterien.json

Evaluation criteria with formal requirements, suitability checks, and award criteria.

### .ofs.index.json

Directory index files tracking document parsing status and available processors.

## Development

### Requirements

- Python >= 3.12

### Project Structure

```
ofs/
├── ofs/                    # Main package
│   ├── cli.py             # Command-line interface
│   ├── core.py            # Main functions
│   ├── config.py          # Configuration system
│   └── [other modules]
├── tests/                 # Test suite
├── setup.py              # Package configuration
└── README.md
```

### Running Tests

```bash
python -m pytest tests/
```

## License

[Add license information here]
