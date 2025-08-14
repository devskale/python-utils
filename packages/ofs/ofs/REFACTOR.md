# OFS Refactoring Plan - Unified Workflow Orchestration

## Overview

This refactoring plan transforms OFS into a central orchestration hub for tender document processing, integrating `pdf2md` parsing and `strukt2meta` metadata generation with intelligent workflow management and AI agentic system support.

## Current State Analysis

### Existing Components
- **pdf2md.skale**: Uses `.pdf2md_index.json` for parsing status tracking
- **strukt2meta**: Intelligent file discovery with parser rankings and OFS integration
- **ofs**: Basic path resolution, project/bidder discovery, limited indexing

### Integration Points
- `strukt2meta` reads `.pdf2md_index.json` files for metadata injection
- Both packages understand OFS structure (A/, B/, md/ directories)
- File discovery systems exist but are not centralized

## Refactoring Goals

### Primary Objectives
1. **Unified Indexing System**: Centralize all file tracking and status management
2. **Workflow Orchestration**: Enable batch processing across different scopes
3. **AI Agentic Support**: Provide structured APIs for AI systems to access tender data
4. **Background Processing**: Implement incremental updates and queue management
5. **Backward Compatibility**: Maintain existing functionality during transition

### Target Architecture
```
OFS Core
├── Unified Index System (.ofs_index.json)
├── Workflow Orchestrator
├── AI Agentic APIs
├── Background Indexing Service
└── Legacy Compatibility Layer
```


## Phase 1: Enhanced Indexing System

### 1.1 Unified Index Schema

Replace `.pdf2md_index.json` with enhanced `.ofs_index.json`:

```json
{
  "schema_version": "2.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "ofs_context": {
    "project": "2025-04 Lampen",
    "section": "A|B",
    "bidder": "Lampion GmbH",
    "path_type": "project|bidder|document"
  },
  "files": [
    {
      "name": "document.pdf",
      "size": 1024000,
      "hash": "sha256:abc123...",
      "last_modified": "2024-01-15T09:00:00Z",
      "parsing": {
        "status": "parsed|unparsed|failed|queued",
        "parsers": {
          "detected": ["marker", "docling", "pdfplumber"],
          "default": "marker",
          "last_used": "marker",
          "results": {
            "marker": {
              "status": "completed",
              "timestamp": "2024-01-15T09:15:00Z",
              "output_file": "document.marker.md",
              "quality_score": 0.95
            },
            "docling": {
              "status": "completed",
              "timestamp": "2024-01-15T09:20:00Z",
              "output_file": "document.docling.md",
              "quality_score": 0.88
            }
          }
        },
        "markdown_files": ["document.marker.md", "document.docling.md"]
      },
      "metadata": {
        "status": "metified|un-metified|failed|queued",
        "last_prompt": "bdok",
        "timestamp": "2024-01-15T10:00:00Z",
        "fields": {
          "kategorie": "Angebot",
          "zusammenfassung": "...",
          "aussteller": "Bidder Name",
          "beschreibung": "Document description"
        },
        "confidence_score": 0.92
      },
      "ai_context": {
        "document_type": "tender_document|bidder_document|criteria|attachment",
        "language": "de",
        "page_count": 15,
        "extracted_entities": [
          {"type": "organization", "value": "Wiener Wohnen", "confidence": 0.98},
          {"type": "date", "value": "2025-06-16", "confidence": 0.95}
        ],
        "keywords": ["Leuchten", "Ausschreibung", "Vergabe"]
      }
    }
  ],
  "directories": [
    {
      "name": "md",
      "type": "processing_output",
      "file_count": 25,
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "processing_queues": {
    "unparsed_pdfs": ["file1.pdf", "file2.pdf"],
    "un_metified_files": ["file3.pdf", "file4.pdf"],
    "failed_parsing": ["corrupted.pdf"],
    "failed_metadata": ["complex.pdf"]
  },
  "statistics": {
    "total_files": 50,
    "parsed_files": 45,
    "metified_files": 40,
    "parsing_success_rate": 0.90,
    "metadata_success_rate": 0.89
  }
}
```

### 1.2 Index Management API

```python
class OFSIndexManager:
    def __init__(self, directory_path: str):
        self.directory_path = Path(directory_path)
        self.index_file = self.directory_path / ".ofs_index.json"
    
    def load_index(self) -> Dict[str, Any]:
        """Load existing index or create new one"""
    
    def update_file_status(self, filename: str, status_type: str, status_data: Dict):
        """Update parsing or metadata status for a file"""
    
    def get_processing_queue(self, queue_type: str) -> List[str]:
        """Get files needing processing"""
    
    def mark_file_processed(self, filename: str, processor: str, result: Dict):
        """Mark file as processed with results"""
    
    def get_file_metadata(self, filename: str) -> Optional[Dict]:
        """Get metadata for a specific file"""
    
    def migrate_from_pdf2md_index(self, pdf2md_index_path: str):
        """Migrate existing .pdf2md_index.json to new format"""
```

## Phase 2: Workflow Orchestration

### 2.1 Workflow Engine

```python
class OFSWorkflowOrchestrator:
    def __init__(self, base_directory: str):
        self.base_dir = Path(base_directory)
        self.index_manager = OFSIndexManager
    
    def run_background_indexing(self, recursive: bool = True):
        """Scan directory tree and update indexes"""
    
    def process_parsing_queue(self, scope: str = "all", max_files: int = None):
        """Process unparsed PDFs using pdf2md"""
    
    def process_metadata_queue(self, scope: str = "all", max_files: int = None):
        """Process un-metified files using strukt2meta"""
    
    def run_full_workflow(self, scope: str, mode: str = "incremental"):
        """Run complete workflow: index -> parse -> metify"""
    
    def get_workflow_status(self, project: str = None) -> Dict:
        """Get current workflow status and statistics"""
```

### 2.2 Processing Scopes

- **Single File**: `ofs workflow process-file /path/to/file.pdf`
- **Bidder Scope**: `ofs workflow process-bidder "2025-04 Lampen" "Lampion GmbH"`
- **Project Section**: `ofs workflow process-section "2025-04 Lampen" "A"`
- **Full Project**: `ofs workflow process-project "2025-04 Lampen"`
- **Full Tree**: `ofs workflow process-all`

### 2.3 Queue Management

```python
class QueueManager:
    def prioritize_files(self, files: List[str], criteria: Dict) -> List[str]:
        """Prioritize files based on size, type, modification time"""
    
    def estimate_processing_time(self, queue: List[str]) -> Dict:
        """Estimate processing time for queue"""
    
    def get_queue_statistics(self) -> Dict:
        """Get queue statistics across all projects"""
```

## Phase 3: AI Agentic System APIs

### 3.1 Structured Data Access

```python
class OFSAgenticAPI:
    """API designed for AI agents to access tender data"""
    
    def get_project_overview(self, project_name: str) -> Dict:
        """Get complete project metadata and status"""
        return {
            "project_metadata": self._load_projekt_meta(project_name),
            "criteria": self._load_kriterien_meta(project_name),
            "processing_status": self._get_processing_status(project_name),
            "document_summary": self._get_document_summary(project_name)
        }
    
    def search_documents(self, query: Dict) -> List[Dict]:
        """Search documents across projects with structured filters"""
        # Support filters: project, bidder, category, keywords, date_range
    
    def get_document_content(self, document_path: str, format: str = "markdown") -> Dict:
        """Get document content in specified format"""
        # Support formats: markdown, json_metadata, raw_text, structured
    
    def get_bidder_analysis(self, project: str, bidder: str) -> Dict:
        """Get comprehensive bidder document analysis"""
        return {
            "documents": self._get_bidder_documents(project, bidder),
            "compliance_status": self._check_compliance(project, bidder),
            "missing_documents": self._identify_missing_docs(project, bidder),
            "quality_scores": self._calculate_quality_scores(project, bidder)
        }
    
    def get_criteria_compliance(self, project: str, bidder: str = None) -> Dict:
        """Check criteria compliance for project or specific bidder"""
    
    def get_processing_recommendations(self, scope: str) -> List[Dict]:
        """Get AI recommendations for processing priorities"""
```

### 3.2 Real-time Status APIs

```python
class OFSStatusAPI:
    def get_global_status(self) -> Dict:
        """Get system-wide processing status"""
        return {
            "total_projects": 15,
            "active_projects": 8,
            "total_documents": 1250,
            "parsed_documents": 1100,
            "metified_documents": 950,
            "processing_queues": {
                "parsing": 45,
                "metadata": 78,
                "failed": 12
            },
            "last_update": "2024-01-15T10:30:00Z"
        }
    
    def get_project_health(self, project: str) -> Dict:
        """Get project health metrics"""
    
    def get_processing_bottlenecks(self) -> List[Dict]:
        """Identify processing bottlenecks and recommendations"""
```

### 3.3 Semantic Search Integration

```python
class OFSSemanticSearch:
    def index_documents_for_search(self, project: str = None):
        """Create semantic search index from processed documents"""
    
    def semantic_search(self, query: str, filters: Dict = None) -> List[Dict]:
        """Perform semantic search across documents"""
    
    def find_similar_documents(self, document_path: str, limit: int = 10) -> List[Dict]:
        """Find documents similar to given document"""
    
    def extract_key_concepts(self, project: str) -> Dict:
        """Extract key concepts and entities from project documents"""
```

## Phase 4: Background Processing Service

### 4.1 Incremental Update System

```python
class OFSBackgroundService:
    def __init__(self, watch_directories: List[str]):
        self.watch_dirs = watch_directories
        self.file_watcher = FileSystemWatcher()
    
    def start_monitoring(self):
        """Start background file system monitoring"""
    
    def handle_file_change(self, event: FileSystemEvent):
        """Handle file system changes (new, modified, deleted files)"""
    
    def schedule_processing(self, file_path: str, priority: int = 5):
        """Schedule file for processing with priority"""
    
    def run_maintenance_tasks(self):
        """Run periodic maintenance (cleanup, optimization, health checks)"""
```

### 4.2 Change Detection

- **File Hash Monitoring**: Detect content changes via SHA256 hashing
- **Timestamp Tracking**: Monitor file modification times
- **Index Validation**: Verify index consistency with file system
- **Orphan Detection**: Identify orphaned markdown files or metadata

## Phase 5: Enhanced CLI Interface

### 5.1 Unified Commands

```bash
# Project Management
ofs project list
ofs project status "2025-04 Lampen"
ofs project create "New Project"
ofs project archive "Old Project"

# Workflow Operations
ofs workflow index --recursive --scope "2025-04 Lampen"
ofs workflow parse --queue --max-files 10
ofs workflow metify --bidder "Lampion GmbH" --prompt "bdok"
ofs workflow run-all --project "2025-04 Lampen"

# Status and Monitoring
ofs status global
ofs status project "2025-04 Lampen"
ofs status queues
ofs health check

# AI Agentic Operations
ofs agent search --query "Leuchten specifications"
ofs agent analyze-bidder "2025-04 Lampen" "Lampion GmbH"
ofs agent compliance-check "2025-04 Lampen"
ofs agent recommendations

# Background Service
ofs service start
ofs service stop
ofs service status
ofs service logs
```

### 5.2 Configuration Management

```json
{
  "ofs_config": {
    "base_directory": ".dir",
    "index_file_name": ".ofs_index.json",
    "background_service": {
      "enabled": true,
      "scan_interval": 300,
      "max_concurrent_jobs": 4
    },
    "processing": {
      "default_parsers": ["marker", "docling"],
      "default_metadata_prompt": "metadata_extraction",
      "quality_threshold": 0.8
    },
    "ai_agentic": {
      "semantic_search_enabled": true,
      "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
      "max_search_results": 50
    }
  }
}
```

## Phase 6: Migration Strategy

### 6.1 Backward Compatibility

1. **Legacy Index Support**: Continue reading `.pdf2md_index.json` files
2. **Gradual Migration**: Migrate indexes on first access
3. **API Compatibility**: Maintain existing function signatures
4. **Configuration Bridge**: Support both old and new config formats

### 6.2 Migration Tools

```bash
# Migrate existing indexes
ofs migrate indexes --from pdf2md --backup

# Validate migration
ofs migrate validate --project "2025-04 Lampen"

# Rollback if needed
ofs migrate rollback --project "2025-04 Lampen"
```

## Implementation Timeline

### Week 1-2: Phase 1 (Enhanced Indexing)
- [ ] Design and implement unified index schema
- [ ] Create OFSIndexManager class
- [ ] Implement migration from .pdf2md_index.json
- [ ] Add comprehensive tests

### Week 3-4: Phase 2 (Workflow Orchestration)
- [ ] Implement OFSWorkflowOrchestrator
- [ ] Create queue management system
- [ ] Add processing scope support
- [ ] Integrate with pdf2md and strukt2meta

### Week 5-6: Phase 3 (AI Agentic APIs)
- [ ] Design and implement OFSAgenticAPI
- [ ] Create structured data access methods
- [ ] Add semantic search capabilities
- [ ] Implement real-time status APIs

### Week 7-8: Phase 4 (Background Processing)
- [ ] Implement background service
- [ ] Add file system monitoring
- [ ] Create incremental update system
- [ ] Add maintenance tasks

### Week 9-10: Phase 5 (Enhanced CLI)
- [ ] Redesign CLI interface
- [ ] Implement unified commands
- [ ] Add configuration management
- [ ] Create comprehensive help system

### Week 11-12: Phase 6 (Migration & Testing)
- [ ] Implement migration tools
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Performance optimization

## Success Metrics

### Technical Metrics
- **Processing Efficiency**: 90% reduction in redundant processing
- **API Response Time**: <100ms for status queries, <500ms for document retrieval
- **Index Consistency**: 99.9% accuracy between index and file system
- **Background Processing**: Real-time updates within 30 seconds of file changes

### User Experience Metrics
- **CLI Usability**: Single command for complex workflows
- **AI Integration**: Structured APIs enabling advanced AI agent capabilities
- **Monitoring**: Real-time visibility into processing status
- **Reliability**: 99.5% uptime for background services

## Risk Mitigation

### Technical Risks
1. **Data Loss**: Comprehensive backup strategy and migration validation
2. **Performance**: Incremental processing and efficient indexing
3. **Compatibility**: Extensive testing with existing workflows
4. **Complexity**: Modular design with clear separation of concerns

### Operational Risks
1. **Migration Issues**: Gradual rollout with rollback capabilities
2. **User Adoption**: Maintain backward compatibility during transition
3. **Resource Usage**: Configurable processing limits and monitoring
4. **Maintenance**: Automated health checks and self-healing capabilities

## Future Enhancements

### Advanced AI Features
- **Intelligent Document Classification**: Auto-categorization using ML models
- **Quality Assessment**: Automated document quality scoring
- **Anomaly Detection**: Identify unusual patterns in tender documents
- **Predictive Analytics**: Forecast processing times and resource needs

### Integration Capabilities
- **External APIs**: Integration with tender platforms and databases
- **Webhook Support**: Real-time notifications for external systems
- **Export Formats**: Support for various output formats (Excel, CSV, XML)
- **Cloud Storage**: Integration with cloud storage providers

### Scalability Features
- **Distributed Processing**: Support for multi-node processing
- **Load Balancing**: Intelligent workload distribution
- **Caching**: Advanced caching for frequently accessed data
- **Monitoring**: Comprehensive metrics and alerting

---

## Conclusion

This refactoring plan transforms OFS from a basic path resolution tool into a comprehensive workflow orchestration platform optimized for AI agentic systems. The unified indexing system, background processing, and structured APIs will enable sophisticated AI agents to efficiently access, analyze, and process tender documents while maintaining the flexibility and reliability required for production use.

The phased approach ensures minimal disruption to existing workflows while progressively adding powerful new capabilities. The focus on AI agentic system support positions OFS as a foundational platform for advanced tender analysis and automated compliance checking.