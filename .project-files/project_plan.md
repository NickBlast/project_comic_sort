# Comic Collection Migration & Normalization - Implementation Plan

## Executive Summary

This plan provides a comprehensive, phased approach to migrate and normalize a large digital collection of Western comics, manga, and hentai/doujin into a consistent structure for use with Komga and Mylar3. The plan emphasizes safety, reversibility, metadata-first design, and cross-platform compatibility (Unraid/Linux/macOS/Windows).

The implementation will be in **Python 3** with a clear separation of concerns across 7 phases, from initial project bootstrap through validation and rollback capability.

---

## Project Structure

### Proposed Directory Layout

```
project_comic_sort/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration loading and validation
│   │   ├── logger.py            # Centralized logging setup
│   │   ├── inventory.py         # File hashing and inventory management
│   │   └── confidence.py        # Confidence level assignment logic
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract base classes for metadata providers
│   │   ├── comicinfo.py         # ComicInfo.xml parsing and generation
│   │   ├── western.py           # ComicVine/GCD integration
│   │   ├── manga.py             # AniList/MangaDex/MAL integration
│   │   └── hentai.py            # LANraragi/E-Hentai/nhentai integration
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── filename.py          # Filename pattern parsing
│   │   └── archive.py           # CBZ/CBR archive handling
│   ├── mappers/
│   │   ├── __init__.py
│   │   ├── western.py           # Western comics path/name mapping
│   │   ├── manga.py             # Manga path/name mapping
│   │   └── hentai.py            # Hentai/doujin path/name mapping
│   ├── operations/
│   │   ├── __init__.py
│   │   ├── scanner.py           # Directory scanning and discovery
│   │   ├── enricher.py          # Metadata enrichment orchestration
│   │   ├── migrator.py          # File copy/move operations
│   │   └── validator.py         # Post-migration validation
│   └── cli/
│       ├── __init__.py
│       ├── inventory.py         # Phase 1 CLI commands
│       ├── enrich.py            # Phase 2 CLI commands
│       ├── map.py               # Phase 3 CLI commands
│       ├── report.py            # Phase 4 CLI commands
│       ├── migrate.py           # Phase 5 CLI commands
│       └── validate.py          # Phase 6 CLI commands
├── config/
│   ├── example_config.yml       # Template configuration with all options
│   ├── paths.example.yml        # Example path configuration
│   └── metadata_sources.yml     # API endpoints and credentials template
├── docs/
│   ├── README.md                # Project overview and quick start
│   ├── agent_instructions.md    # AI coding agent guidelines
│   ├── metadata_strategy.md     # Detailed metadata handling docs
│   ├── confidence_levels.md     # Confidence level system explanation
│   └── troubleshooting.md       # Common issues and solutions
├── logs/
│   └── .gitkeep                 # Logs will be created here at runtime
├── output/
│   ├── inventories/             # Pre/post migration inventories
│   ├── mappings/                # Generated mapping tables
│   ├── reports/                 # Dry-run and validation reports
│   └── ledgers/                 # Failure and learning logs
├── tests/
│   ├── __init__.py
│   ├── test_parsers.py
│   ├── test_metadata.py
│   ├── test_mappers.py
│   └── fixtures/                # Sample files for testing
├── scripts/
│   ├── bootstrap.py             # Initial environment setup script
│   └── rollback.py              # Emergency rollback script
├── .gitignore
├── requirements.txt             # Python dependencies
├── requirements-dev.txt         # Development dependencies
└── README.md                    # Project root README
```

### Purpose of Key Directories

- **`src/core/`**: Cross-cutting concerns (config, logging, inventory, confidence)
- **`src/metadata/`**: All metadata provider integrations and ComicInfo.xml handling
- **`src/parsers/`**: Filename parsing and archive file handling
- **`src/mappers/`**: Logic to determine target paths from metadata
- **`src/operations/`**: High-level orchestration of scanning, enrichment, migration, validation
- **`src/cli/`**: Command-line interfaces for each phase
- **`config/`**: Configuration templates (never containing real credentials)
- **`docs/`**: All documentation including agent instructions
- **`logs/`**: Runtime logs (excluded from git)
- **`output/`**: All generated artifacts (inventories, mappings, reports, ledgers)
- **`tests/`**: Unit and integration tests
- **`scripts/`**: Standalone utility scripts

---

## Baseline Configuration Files

### 1. `config/example_config.yml`

**Purpose**: Primary configuration template covering all system settings.

**Conceptual sections**:
- `environment`: Operating mode (dry_run vs apply), Python version requirements
- `paths`: Source library roots, target library roots, temp directories
- `safety`: Backup requirements, permission checks, operation timeouts
- `logging`: Log levels, log file paths, rotation settings
- `metadata_providers`: Enable/disable flags for ComicVine, AniList, LANraragi, etc.
- `confidence`: Thresholds for high/medium/low confidence assignments
- `naming`: Patterns for Western comics, manga, hentai (templates with placeholders)
- `komga`: Library configuration hints
- `mylar3`: Folder/file format strings

### 2. `config/paths.example.yml`

**Purpose**: Isolate path configuration for easy environment-specific overrides.

**Conceptual sections**:
- `source_libraries`: List of existing library paths to scan
- `target_roots`: `/media/Comics`, `/media/Manga`, `/media/H-Manga`
- `temp_workspace`: Where to store intermediate files
- `backup_location`: Optional backup destination

### 3. `config/metadata_sources.yml`

**Purpose**: API configuration and credentials (template only).

**Conceptual sections**:
- `comicvine`: API key placeholder, rate limits
- `anilist`: OAuth setup notes, API endpoints
- `mangadex`: API version, endpoints
- `lanraragi`: URL, API key placeholder, connection timeout
- `nhentai`: API notes (if direct API, mostly fallback to filename parsing)
- `e_hentai`: Cookie/session management notes

### 4. `docs/agent_instructions.md`

**Purpose**: Guidelines for AI coding agents extending or maintaining this project.

**Conceptual sections**:

**Coding Standards**:
- Use `pathlib.Path` for all path operations
- Type hints required for all functions
- Docstrings in Google format
- Maximum line length: 100 characters
- Use `black` for formatting, `pylint` for linting

**Architecture Patterns**:
- Provider pattern for metadata sources (inherit from `BaseMetadataProvider`)
- Factory pattern for mapper selection based on content type
- Strategy pattern for confidence level assignment
- Repository pattern for inventory/ledger persistence

**Configuration Handling**:
- All config loaded via `src/core/config.py`
- Use `pydantic` for config validation
- Environment variables override config file values
- Never hardcode paths or credentials

**Logging Standards**:
- Use `src/core/logger.py` exclusively
- Log levels: DEBUG (verbose), INFO (progress), WARN (recoverable), ERROR (failures)
- Always log before and after destructive operations
- Include context: file paths, operation type, confidence level

**Dry-Run vs Apply Mode**:
- All operations must check `config.environment.dry_run` flag
- Dry-run: Log intended action, update in-memory state, write to report files only
- Apply: Perform actual file operations, log success/failure, update ledgers
- Default must always be dry-run

**Error Handling**:
- Catch specific exceptions, never bare `except:`
- Log full stack trace at ERROR level
- Record failure in ledger with structured data
- Continue processing other files (fail gracefully)

**Testing Requirements**:
- Unit tests for all parsers and mappers
- Integration tests with fixture files
- Mock external API calls in tests
- Test both dry-run and apply modes

**Metadata Provider Integration**:
- Must implement `BaseMetadataProvider` interface
- Must handle rate limiting
- Must return confidence level with results
- Must handle API unavailability gracefully

**File Operations Safety**:
- Never delete originals unless explicitly configured
- Always verify target path doesn't exist before copy
- Use atomic operations where possible
- Compute hash before and after copy to verify integrity

---

## Logging & Failure Handling Design

### Structured Logging Scheme

**Log Files**:
1. `logs/operations_{timestamp}.log`: All operations (INFO and above)
2. `logs/debug_{timestamp}.log`: Verbose debug output (DEBUG and above)
3. `logs/errors_{timestamp}.log`: Errors only (ERROR level)

**Log Entry Format** (JSON Lines):
```json
{
  "timestamp": "2025-01-15T14:30:00Z",
  "level": "INFO",
  "phase": "metadata_enrichment",
  "operation": "fetch_comicvine",
  "file_path": "/source/comics/batman_001.cbz",
  "message": "Successfully retrieved metadata",
  "metadata": {
    "series": "Batman",
    "issue": "1",
    "confidence": "high"
  }
}
```

### Failure & Learning Ledger

**File**: `output/ledgers/processing_ledger.jsonl` (JSON Lines format)

**Per-Item Record**:
```json
{
  "file_path": "/source/comics/unknown_comic.cbz",
  "sha256": "abc123...",
  "timestamp": "2025-01-15T14:30:00Z",
  "phase": "metadata_enrichment",
  "operation": "comicvine_lookup",
  "status": "best_guess",
  "confidence": "medium",
  "metadata_source": "filename_parsing",
  "target_path": "/media/Comics/Unknown Publisher/Unknown Series (2020)/Unknown Series (2020) #001.cbz",
  "reasoning": "No ComicVine match; parsed year from filename pattern",
  "errors": [],
  "retry_count": 0,
  "requires_review": true
}
```

**Status Values**: `success`, `best_guess`, `failed`, `skipped`, `pending_retry`

### Ledger Processing Logic

**On Each Script Run**:
1. Load existing ledger
2. Filter to items relevant for current phase
3. Skip items with `status: success` unless forcing re-processing
4. Retry items with `status: pending_retry` and `retry_count < max_retries`
5. Surface items with `requires_review: true` in reports
6. Append new records for newly processed items
7. Update records for retried items

**Retry Logic**:
- Transient errors (network timeouts, rate limits): Automatic retry with exponential backoff
- Persistent errors (404 not found, parsing failures): Mark for manual review, don't retry
- Maximum 3 retry attempts per item per phase

**Review Queue**:
- Generate `output/reports/needs_review_{timestamp}.csv` with all `requires_review: true` items
- Include columns: file_path, confidence, reasoning, target_path, suggested_action
- Allow manual override file: `config/manual_overrides.yml` to provide corrections

---

## OS-Specific Considerations

### Cross-Platform Path Handling

**Strategy**:
- Use `pathlib.Path` exclusively (never `os.path`)
- Convert all path strings to `Path` objects immediately upon input
- Use `Path.resolve()` to normalize paths (handles symlinks, `.` and `..`)
- Use `Path.as_posix()` for logging/display (consistent forward slashes)
- Use `Path.stat()` for cross-platform file metadata

**Windows-Specific**:
- Handle long path names (>260 chars) with `\\?\` prefix if needed
- Case-insensitive filesystem considerations in conflict detection
- NTFS alternate data streams are ignored

**Unraid/Linux/macOS**:
- Respect case-sensitive filesystems
- Handle spaces and special characters in filenames (quote paths in shell commands if needed)
- Preserve Unix permissions when copying (use `shutil.copy2` instead of `shutil.copy`)

### Archive Handling

**Libraries**: Use `py7zr` for 7z, `zipfile` (built-in) for CBZ, `rarfile` for CBR

**Platform Notes**:
- CBR (RAR) requires `unrar` binary installed on system
- Detection: Use `shutil.which('unrar')` to check availability
- Fallback: Log warning if RAR files found but `unrar` not available
- Conversion option: Offer to convert CBR → CBZ in Phase 2

### Docker/Container Considerations

**Path Mapping**:
- Document that host paths may differ from container paths
- Config should use container-internal paths
- Volume mounts must be configured correctly before running
- Include Docker Compose example in `docs/`

**Permissions**:
- Scripts should detect if running in container via environment variable
- Handle UID/GID mapping issues (files created as root vs host user)
- Use `chown` after file operations if needed (container mode only)

---

## Integration Notes

### Komga Integration

**Library Configuration**:
- One Komga library per root: Comics, Manga, H-Manga
- Each leaf folder = one Series
- ComicInfo.xml required for proper metadata display

**Validation Steps** (Phase 6):
1. API call to Komga to trigger library scan
2. Query Komga API for series count and compare to expected
3. Spot-check 10 random series for correct metadata display
4. Check for duplicate series detection

**Komga API Requirements**:
- Komga URL and API key in `config/metadata_sources.yml`
- Use `requests` library with retry logic
- Endpoints: `/api/v1/libraries/{id}/scan`, `/api/v1/series`

### Mylar3 Integration

**Configuration Alignment**:
- Mylar3 Folder Format should match: `<Publisher>/<Series> (<StartYear>)`
- Mylar3 File Format should match: `Series (Year) #NNN (YYYY-MM-DD)`
- Comic Location: `/media/Comics`

**Validation Steps** (Phase 6):
1. Export Mylar3 database or use API to list series
2. Check that series paths exist in new structure
3. Verify issue numbering matches
4. Optional: Update Mylar3 database paths programmatically via API

**Mylar3 API Requirements**:
- Mylar3 URL and API key in config
- Endpoints: `/api?cmd=getComicList`, `/api?cmd=getComic`

### LANraragi Integration

**Configuration**:
- LANraragi URL and API key
- Connection test on startup
- If unreachable: Log warning, proceed with fallback

**Metadata Retrieval** (Phase 2):
1. Query LANraragi by filename or internal ID
2. Parse LANraragi tags into ComicInfo.xml fields:
   - `tags: artist:name` → `<Writer>` and `<Penciller>`
   - `tags: parody:name` → `<Series>`
   - `tags: language:name` → `<LanguageISO>`
   - `tags: group:name` → `<Publisher>` (circle name)
3. Assign high confidence if LANraragi has E-Hentai/nhentai ID
4. Store LANraragi ID in ComicInfo.xml `<Notes>` for future reference

**Fallback (No LANraragi)**:
- Parse filename for patterns: `[CircleName] (ID) Title (Language) [Source].cbz`
- Extract artist/circle from brackets
- Extract ID from parentheses (nhentai ID, e-hentai gallery ID)
- Assign medium confidence
- Log that LANraragi unavailable, metadata incomplete

**LANraragi API Calls**:
- `GET /api/archives`: List all archives
- `GET /api/archives/{id}/metadata`: Get metadata for specific archive
- Use `requests` with timeout and retry

---

## Confidence Level System (Detailed)

### High Confidence (Fully Automated)

**Criteria**:
- Positive ID from trusted API with exact match
- ComicVine: Direct issue match via barcode or UPC
- AniList/MangaDex: Exact series + volume/chapter match
- LANraragi: Archive with verified E-Hentai or nhentai gallery ID

**Actions**:
- Rename and move to final target structure
- Mark as `status: success` in ledger
- No manual review required

**Example Scenarios**:
- Western comic with embedded ComicInfo.xml containing ComicVine ID
- Manga with AniList ID in filename, API confirms volume number
- Hentai doujin with nhentai ID in filename, LANraragi confirms metadata

### Medium Confidence (Best Guess - Flagged)

**Criteria**:
- Metadata inferred from filename parsing with partial API confirmation
- Multiple API matches but one is clearly most relevant
- Metadata provider returns result but with ambiguity (e.g., multiple series with same name)

**Actions**:
- Rename and move to final structure (or optional `_best_guess` subfolder)
- Mark as `status: best_guess` in ledger
- Record reasoning in `reasoning` field
- Flag `requires_review: true`
- Include in `needs_review` report

**Example Scenarios**:
- Filename: `Batman v1 001.cbz` → Multiple "Batman" series on ComicVine, selected most popular
- Manga filename: `One Piece v01.cbz` → Clear series match, but release year ambiguous
- Hentai filename: `[Circle] Title.cbz` → Parsed circle name, but no ID verification

**Best Guess Subfolder Option** (Configurable):
- If `config.confidence.best_guess_separate_folder: true`
- Target: `/media/Comics/_best_guess/<Publisher>/<Series>/<Files>`
- User can review and manually move to parent directory

### Low Confidence / Unknown (Manual Review Required)

**Criteria**:
- No API match found
- Multiple conflicting API matches with no clear winner
- Parsing failed or returned ambiguous results
- Metadata provider error (API down, rate limited)

**Actions**:
- Do NOT rename or move
- Copy to `_unsorted` tree (mirroring original structure): `/media/Comics/_unsorted/original/path/file.cbz`
- Mark as `status: failed` or `status: skipped` in ledger
- Record all attempted strategies and errors
- Flag `requires_review: true`
- Prominently include in `needs_review` report

**Example Scenarios**:
- Filename: `comic001.cbz` with no embedded metadata
- Manga with non-standard naming, no API match
- Corrupted archive that cannot be opened
- API timeout or temporary unavailability

**Unsorted Tree Structure**:
```
/media/Comics/_unsorted/
  ├── original_source_folder_1/
  │   └── ambiguous_comic.cbz
  └── original_source_folder_2/
      └── unknown_issue.cbz
```

### Confidence Assignment Logic (Pseudocode)

```python
def assign_confidence(file_path, metadata, api_results):
    if metadata.comicvine_id and api_results.comicvine.exact_match:
        return "high", "Direct ComicVine ID match"
    
    if metadata.series and api_results.fuzzy_match.score > 0.9:
        return "high", f"Strong fuzzy match (score: {score})"
    
    if metadata.series and api_results.fuzzy_match.score > 0.7:
        return "medium", f"Moderate fuzzy match (score: {score}), best candidate selected"
    
    if metadata.series and len(api_results.candidates) > 1:
        return "medium", f"Multiple matches, selected by heuristic (popularity, year)"
    
    if metadata.series and len(api_results.candidates) == 0:
        if metadata.source == "filename_parsing":
            return "low", "No API match, filename parsing only"
    
    return "low", "Insufficient metadata for confident assignment"
```

---

## Phase Breakdown

### Phase 0 – Project Bootstrap, Environment & Safety Checks

**Objective**: Establish project foundation, validate environment, ensure safe execution prerequisites.

#### Task 0.1: Initialize Project Structure
- **Objective**: Create all directories and placeholder files
- **Inputs**: None (fresh project)
- **Tools**: Python `os.makedirs()` or `pathlib.Path.mkdir()`
- **Outputs**: Complete directory tree as specified above
- **Tests**: Verify all directories exist, `.gitkeep` files in empty dirs

#### Task 0.2: Create Configuration Templates
- **Objective**: Generate `config/example_config.yml`, `config/paths.example.yml`, `config/metadata_sources.yml`
- **Inputs**: Project requirements
- **Tools**: YAML generation (can be static template files)
- **Outputs**: Three config templates with comments explaining each section
- **Tests**: YAML syntax validation with `pyyaml`

#### Task 0.3: Write Agent Instructions Document
- **Objective**: Create `docs/agent_instructions.md`
- **Inputs**: Coding standards, architectural patterns (as outlined above)
- **Outputs**: Comprehensive Markdown document
- **Tests**: Markdown lint, readability check

#### Task 0.4: Initialize Python Environment
- **Objective**: Check Python version, create `requirements.txt`, setup guidance
- **Inputs**: Python 3.8+ requirement
- **Tools**: `sys.version_info` check
- **Outputs**: 
  - `requirements.txt` with: `pyyaml`, `pydantic`, `requests`, `py7zr`, `rarfile`, `pillow`, `lxml`
  - `requirements-dev.txt` with: `pytest`, `black`, `pylint`, `mypy`
- **Tests**: `pip install -r requirements.txt` dry-run

#### Task 0.5: Implement Core Config Loader
- **Objective**: Create `src/core/config.py` to load and validate configuration
- **Inputs**: Config YAML files
- **Tools**: `pydantic` for validation, `pyyaml` for parsing
- **Outputs**: `Config` class with nested models for each section
- **Tests**: Unit tests with valid and invalid config, environment variable override tests

#### Task 0.6: Implement Logging System
- **Objective**: Create `src/core/logger.py` with structured logging
- **Inputs**: Log level and file path from config
- **Tools**: Python `logging` module, JSON formatter
- **Outputs**: Singleton logger instance, log files in `logs/`
- **Tests**: Write test logs at all levels, verify JSON format, rotation

#### Task 0.7: Safety Checks Script
- **Objective**: Create `src/operations/safety_checks.py` to validate environment
- **Inputs**: Config paths
- **Tools**: `pathlib.Path.exists()`, `os.access()` for permissions
- **Checks**:
  - Source paths exist and are readable
  - Target paths are writable (or can be created)
  - Sufficient disk space (estimate based on source size)
  - No overlapping library roots
  - Python version >= 3.8
- **Outputs**: Boolean pass/fail, detailed error messages
- **Tests**: Mock filesystem scenarios (no permission, no space, etc.)

#### Task 0.8: Dry-Run Mode Framework
- **Objective**: Implement config flag and wrapper for file operations
- **Inputs**: `config.environment.dry_run` boolean
- **Tools**: Decorator pattern or context manager
- **Outputs**: `@dry_run_safe` decorator that logs instead of executing in dry-run mode
- **Tests**: Verify file operations are logged but not executed when dry_run=true

---

### Phase 1 – Inventory & Backup

**Objective**: Create complete inventory of existing library with file hashes, establish backup strategy.

#### Task 1.1: Implement File Scanner
- **Objective**: Create `src/operations/scanner.py` to recursively discover comic files
- **Inputs**: Source library paths from config
- **Tools**: `pathlib.Path.rglob()` for recursive search
- **File Extensions**: `.cbz`, `.cbr`, `.cb7`, `.pdf` (comics only, filter out non-comics)
- **Outputs**: List of `Path` objects
- **Tests**: Test with nested directory structure, symlinks, hidden files

#### Task 1.2: Implement Hashing Utility
- **Objective**: Create `src/core/inventory.py` with hash calculation
- **Inputs**: File path
- **Tools**: `hashlib.sha256()`
- **Outputs**: Hex digest string
- **Optimization**: Use chunked reading for large files (8192 byte chunks)
- **Tests**: Verify hash consistency, test with large files (>1GB)

#### Task 1.3: Create Inventory Generator
- **Objective**: Scan all files and generate inventory JSON
- **Inputs**: Scanned file list
- **Tools**: Hashing utility, JSON serialization
- **Outputs**: `output/inventories/pre_migration_{timestamp}.json`
- **Format**:
  ```json
  {
    "timestamp": "2025-01-15T14:30:00Z",
    "total_files": 15000,
    "total_size_bytes": 500000000000,
    "files": [
      {
        "path": "/source/comics/batman_001.cbz",
        "size_bytes": 25000000,
        "sha256": "abc123...",
        "modified_time": "2024-05-10T10:00:00Z"
      }
    ]
  }
  ```
- **Tests**: Verify JSON structure, hash accuracy, handle filesystem errors

#### Task 1.4: Backup Strategy Documentation
- **Objective**: Create `docs/backup_strategy.md` with recommendations
- **Inputs**: User's backup preferences (to be gathered)
- **Content**:
  - Option 1: Copy entire source to backup location before starting
  - Option 2: Use filesystem snapshots (ZFS, Btrfs, Windows Shadow Copy)
  - Option 3: Rely on inventory hashes for verification (riskier)
  - Recommendation: Snapshot if available, else full copy
- **Outputs**: Markdown document
- **Tests**: N/A (documentation)

#### Task 1.5: Implement Backup Verification
- **Objective**: If backup created, verify completeness
- **Inputs**: Backup location, original inventory
- **Tools**: Re-scan backup location, compare inventories
- **Outputs**: Boolean verification result, diff report if mismatch
- **Tests**: Mock backup with missing files, verify detection

#### Task 1.6: CLI for Phase 1
- **Objective**: Create `src/cli/inventory.py` with commands:
  - `inventory scan --source <path> --output <json>`
  - `inventory verify --original <json> --backup <path>`
- **Inputs**: Command-line arguments
- **Tools**: `argparse` or `click`
- **Outputs**: JSON inventory, console progress updates
- **Tests**: End-to-end test with sample directory

---

### Phase 2 – Metadata Enrichment

**Objective**: Detect, fetch, and populate ComicInfo.xml for all archives, assigning confidence levels.

#### Task 2.1: Implement ComicInfo.xml Parser
- **Objective**: Create `src/metadata/comicinfo.py` to read/write ComicInfo.xml
- **Inputs**: Archive file path
- **Tools**: `zipfile` to extract/insert XML, `lxml` to parse
- **Outputs**: `ComicInfo` dataclass with fields: Series, Number, Volume, Year, Publisher, Writer, etc.
- **Tests**: Parse sample ComicInfo.xml files, roundtrip write/read

#### Task 2.2: Implement Base Metadata Provider
- **Objective**: Create `src/metadata/base.py` abstract class
- **Interface**:
  - `search(query: str) -> List[SearchResult]`
  - `get_details(id: str) -> MetadataDetails`
  - `get_confidence(result: SearchResult, file_context: FileContext) -> ConfidenceLevel`
- **Outputs**: Abstract class for inheritance
- **Tests**: N/A (abstract class)

#### Task 2.3: Implement Western Comics Provider
- **Objective**: Create `src/metadata/western.py` for ComicVine/GCD
- **Inputs**: Series name, issue number, year (from filename or existing metadata)
- **Tools**: `requests` for API calls, rate limiting with `ratelimit` library
- **API**: ComicVine API (requires API key)
- **Outputs**: `ComicInfo` object with populated fields, confidence level
- **Confidence Logic**:
  - Exact barcode/UPC match → high
  - Series + issue + year match → high
  - Series + issue match (multiple years) → medium (select by heuristic)
  - Series match only → medium (prompt for issue)
  - No match → low
- **Tests**: Mock API responses, rate limit handling, error cases

#### Task 2.4: Implement Manga Provider
- **Objective**: Create `src/metadata/manga.py` for AniList/MangaDex
- **Inputs**: Series name, volume/chapter (from filename or existing metadata)
- **Tools**: `requests`, GraphQL for AniList
- **API**: AniList GraphQL API, MangaDex REST API
- **Outputs**: `ComicInfo` object adapted for manga (use Volume for tankobon, Number for chapters)
- **Confidence Logic**:
  - Exact AniList/MangaDex ID → high
  - Series + volume match → high
  - Series match with volume inference → medium
  - Ambiguous series name → low
- **Tests**: Mock GraphQL/REST responses, handle Unicode titles

#### Task 2.5: Implement Hentai Provider
- **Objective**: Create `src/metadata/hentai.py` for LANraragi/E-Hentai/nhentai
- **Inputs**: Filename, LANraragi availability flag
- **Tools**: `requests` for LANraragi API, filename regex parsing
- **API**: LANraragi API if configured, else filename parsing
- **Outputs**: `ComicInfo` object with artist, parody, tags
- **Confidence Logic**:
  - LANraragi with gallery ID → high
  - LANraragi without gallery ID but good metadata → medium
  - Filename parsing only → medium (if clear pattern) or low
- **Fallback Patterns**:
  - `[Circle] (ID) Title (Language) [Source].cbz`
  - `(ID) [Circle] Title.cbz`
  - Extract nhentai ID: `(123456)` → query nhentai API if available
- **Tests**: Mock LANraragi API, test regex patterns, unavailable API handling

#### Task 2.6: Implement Filename Parser
- **Objective**: Create `src/parsers/filename.py` with regex patterns
- **Inputs**: Filename string
- **Tools**: `re` module, pre-compiled patterns
- **Patterns**:
  - Western: `Series vN #NNN (YYYY-MM-DD).cbz`
  - Manga: `Series vNN.cbz`, `Series cNNN.cbz`
  - Hentai: Multiple patterns as above
- **Outputs**: Parsed fields dict: `{series, issue, volume, year, publisher, language, etc.}`
- **Tests**: Comprehensive pattern tests, edge cases (special characters, Unicode)

#### Task 2.7: Implement Archive Handler
- **Objective**: Create `src/parsers/archive.py` to open and modify archives
- **Inputs**: Archive file path
- **Tools**: `zipfile`, `py7zr`, `rarfile`
- **Operations**:
  - Open archive (auto-detect format)
  - Extract ComicInfo.xml if exists
  - Insert/update ComicInfo.xml
  - Close archive (preserving compression)
- **Outputs**: Modified archive with updated ComicInfo.xml
- **Tests**: Test all archive formats, handle corrupted archives, verify integrity after modification

#### Task 2.8: Implement Enrichment Orchestrator
- **Objective**: Create `src/operations/enricher.py` to coordinate metadata fetching
- **Inputs**: File path, content type (western/manga/hentai)
- **Process**:
  1. Open archive, check for existing ComicInfo.xml
  2. If exists and complete, assign high confidence, skip API calls
  3. If missing or incomplete:
     - Parse filename
     - Query appropriate provider (western/manga/hentai)
     - Merge results with existing metadata (prefer API over filename)
     - Assign confidence level
  4. Write ComicInfo.xml back to archive
  5. Record operation in ledger
- **Outputs**: Updated archive, ledger entry
- **Tests**: End-to-end with sample files, mock API calls

#### Task 2.9: CLI for Phase 2
- **Objective**: Create `src/cli/enrich.py` with commands:
  - `enrich western --source <path> [--dry-run]`
  - `enrich manga --source <path> [--dry-run]`
  - `enrich hentai --source <path> [--dry-run] [--lanraragi-url <url>]`
- **Inputs**: Command-line arguments, config
- **Outputs**: Updated archives (if not dry-run), ledger updates, progress logs
- **Tests**: End-to-end with sample files

---

### Phase 3 – Mapping Logic

**Objective**: From enriched metadata, compute target paths and filenames, assign final confidence levels.

#### Task 3.1: Implement Western Comics Mapper
- **Objective**: Create `src/mappers/western.py`
- **Inputs**: `ComicInfo` object
- **Template**: `/media/Comics/<Publisher>/<Series> (<StartYear>)/Series (Year) #NNN (YYYY-MM-DD).cbz`
- **Logic**:
  - Publisher from metadata, fallback to "Unknown Publisher"
  - Series from metadata
  - StartYear: First issue year or series start year from API
  - Issue number: Zero-padded to 3 digits
  - Date: From metadata if available, else "YYYY-00-00"
- **Outputs**: Target `Path` object
- **Tests**: Various metadata combinations, handle missing fields

#### Task 3.2: Implement Manga Mapper
- **Objective**: Create `src/mappers/manga.py`
- **Inputs**: `ComicInfo` object
- **Template**: `/media/Manga/<Series>/<Series> vNN.cbz` or `<Series> cNNN.cbz`
- **Logic**:
  - Use volume number for tankobon: `v01`, `v02` (zero-padded to 2 digits)
  - Use chapter number for serialized chapters: `c001`, `c002` (zero-padded to 3 digits)
  - Decision: If metadata has `Volume`, use vNN; if only `Number`, use cNNN
- **Outputs**: Target `Path` object
- **Tests**: Volume vs chapter scenarios, one-shots

#### Task 3.3: Implement Hentai Mapper
- **Objective**: Create `src/mappers/hentai.py`
- **Inputs**: `ComicInfo` object, LANraragi metadata
- **Template Options**:
  - One-shot: `/media/H-Manga/_oneshots/(ID) - Title (Language) [Source].cbz`
  - Series: `/media/H-Manga/[CircleName]/Series Title/Series vNN.cbz`
- **Logic**:
  - Detect one-shot: No series/parody tag, single volume
  - Extract circle name from metadata tags or filename
  - Include language code if non-English
  - Include source (nhentai, e-hentai, etc.) if known
- **Outputs**: Target `Path` object
- **Tests**: One-shot vs series, various tag combinations

#### Task 3.4: Implement Confidence Re-Evaluation
- **Objective**: Create `src/core/confidence.py` with final confidence assignment
- **Inputs**: Metadata source, API match quality, mapping success
- **Logic**: Re-confirm confidence level based on mapping results
  - If mapping failed (missing critical fields): Downgrade to low
  - If mapping succeeded but used defaults: Stay at medium
  - If mapping succeeded with all fields from API: Confirm high
- **Outputs**: Final confidence level
- **Tests**: Various confidence scenarios

#### Task 3.5: Implement Conflict Detection
- **Objective**: Detect when multiple source files map to same target path
- **Inputs**: Mapping table (all source → target pairs)
- **Logic**:
  - Group by target path
  - If multiple sources: Flag as conflict
  - Suggest resolution: Append `-alt`, `-v2`, etc. or manual review
- **Outputs**: Conflict report JSON
- **Tests**: Create intentional conflicts, verify detection

#### Task 3.6: Generate Mapping Table
- **Objective**: Create complete mapping CSV/JSON for all files
- **Inputs**: Enriched metadata for all files
- **Tools**: Call appropriate mapper based on content type
- **Outputs**: `output/mappings/mapping_{timestamp}.csv`
- **Format**:
  ```csv
  source_path,target_path,confidence,metadata_source,content_type,conflict
  /source/comics/batman.cbz,/media/Comics/DC/Batman (1940)/Batman (1940) #001 (1940-04-25).cbz,high,comicvine,western,false
  ```
- **Tests**: Verify all files mapped, confidence distribution report

#### Task 3.7: CLI for Phase 3
- **Objective**: Create `src/cli/map.py` with commands:
  - `map generate --inventory <json> --output <csv> [--content-type <type>]`
  - `map conflicts --mapping <csv>`
- **Inputs**: Inventory JSON, enriched metadata
- **Outputs**: Mapping CSV, conflict report
- **Tests**: End-to-end mapping generation

---

### Phase 4 – Dry-Run Reporting

**Objective**: Generate human-readable reports of proposed changes without executing them.

#### Task 4.1: Implement Report Generator
- **Objective**: Create `src/operations/reporter.py`
- **Inputs**: Mapping table, ledger
- **Outputs**: Multiple report files in `output/reports/`

#### Task 4.2: Summary Report
- **File**: `output/reports/summary_{timestamp}.txt`
- **Contents**:
  - Total files: X
  - High confidence: Y (Z%)
  - Medium confidence: Y (Z%)
  - Low confidence: Y (Z%)
  - Conflicts detected: N
  - Estimated disk usage: X GB
  - Estimated runtime: X hours (based on file count and copy speed)

#### Task 4.3: Confidence Breakdown Report
- **File**: `output/reports/confidence_breakdown_{timestamp}.csv`
- **Contents**: List of all medium and low confidence items with reasoning
- **Columns**: source_path, confidence, reasoning, proposed_target, content_type

#### Task 4.4: Conflicts Report
- **File**: `output/reports/conflicts_{timestamp}.csv`
- **Contents**: All conflicting mappings
- **Columns**: target_path, source_path_1, source_path_2, ..., suggested_resolution

#### Task 4.5: Unsorted Items Report
- **File**: `output/reports/unsorted_{timestamp}.csv`
- **Contents**: All low-confidence items that will go to `_unsorted`
- **Columns**: source_path, reason, attempted_strategies, error_messages

#### Task 4.6: Best Guess Report
- **File**: `output/reports/best_guess_{timestamp}.csv`
- **Contents**: All medium-confidence items
- **Columns**: source_path, proposed_target, reasoning, metadata_fields_used, review_priority

#### Task 4.7: Visualization (Optional)
- **Objective**: Generate simple HTML report with charts
- **Tools**: `matplotlib` or `plotly` for charts
- **Charts**:
  - Confidence level pie chart
  - Content type distribution bar chart
  - File size distribution histogram
- **Output**: `output/reports/visual_report_{timestamp}.html`

#### Task 4.8: CLI for Phase 4
- **Objective**: Create `src/cli/report.py` with commands:
  - `report generate --mapping <csv> --output-dir <path>`
  - `report summary --mapping <csv>`
- **Inputs**: Mapping CSV, ledger
- **Outputs**: All report files
- **Tests**: Verify report generation, check readability

---

### Phase 5 – Execution (Copy/Rename/Move)

**Objective**: Execute file operations based on mapping table, respecting confidence levels and dry-run mode.

#### Task 5.1: Implement Safe Copy Operation
- **Objective**: Create `src/operations/migrator.py` with copy function
- **Inputs**: Source path, target path
- **Tools**: `shutil.copy2()` to preserve metadata
- **Safety Checks**:
  - Verify source exists
  - Verify target doesn't exist (or prompt for overwrite)
  - Verify target directory exists (create if not)
  - Verify sufficient disk space
- **Post-Copy**:
  - Compute hash of copy
  - Compare with original hash
  - If mismatch: Delete copy, log error, mark as failed
- **Outputs**: Boolean success, copied file
- **Tests**: Test copy, verify integrity, handle errors

#### Task 5.2: Implement Confidence-Based Migration Strategy
- **Objective**: Route files based on confidence level
- **Inputs**: Mapping table row, config
- **Logic**:
  - **High confidence**: Copy to final target path
  - **Medium confidence**:
    - If `config.confidence.best_guess_separate_folder: true`: Copy to `_best_guess` subfolder
    - Else: Copy to final target path
  - **Low confidence**: Copy to `_unsorted` path (preserve original structure)
- **Outputs**: Copied files in appropriate locations
- **Tests**: Verify routing for each confidence level

#### Task 5.3: Implement Batch Processor
- **Objective**: Process mapping table in batches with progress tracking
- **Inputs**: Mapping CSV, batch size (e.g., 100 files)
- **Tools**: Progress bar with `tqdm`
- **Process**:
  - Read mapping table
  - Filter by confidence level (if specified)
  - Process in batches
  - Update ledger after each batch
  - Handle interruptions gracefully (resume capability)
- **Outputs**: Migrated files, updated ledger
- **Tests**: Test interruption and resume, verify batch processing

#### Task 5.4: Implement Ledger Updates
- **Objective**: Record every operation in ledger
- **Inputs**: Operation result (success/failure), source path, target path
- **Outputs**: Appended ledger entry
- **Format**: As defined in Logging section
- **Tests**: Verify ledger entries, concurrent access handling

#### Task 5.5: Implement Post-Migration Inventory
- **Objective**: Generate inventory of migrated files
- **Inputs**: Target library roots
- **Tools**: Same scanner as Phase 1
- **Outputs**: `output/inventories/post_migration_{timestamp}.json`
- **Tests**: Compare with expected file count from mapping

#### Task 5.6: Handle CBR to CBZ Conversion (Optional)
- **Objective**: Optionally convert CBR files to CBZ during migration
- **Inputs**: Config flag `config.operations.convert_cbr_to_cbz`
- **Tools**: Extract CBR with `rarfile`, repackage as CBZ with `zipfile`
- **Outputs**: CBZ files instead of CBR
- **Tests**: Verify conversion, preserve image quality, check ComicInfo.xml transfer

#### Task 5.7: CLI for Phase 5
- **Objective**: Create `src/cli/migrate.py` with commands:
  - `migrate execute --mapping <csv> --confidence <level> [--dry-run]`
  - `migrate resume --ledger <jsonl>` (resume interrupted migration)
- **Inputs**: Mapping CSV, config
- **Outputs**: Migrated files, ledger updates, progress logs
- **Tests**: End-to-end migration, dry-run verification

---

### Phase 6 – Validation (Komga/Mylar3)

**Objective**: Verify migration success, integrate with Komga and Mylar3.

#### Task 6.1: Implement Inventory Comparison
- **Objective**: Compare pre- and post-migration inventories
- **Inputs**: Pre-migration JSON, post-migration JSON
- **Tools**: JSON diff
- **Checks**:
  - File count matches (accounting for unsorted items)
  - All high-confidence files present in target
  - No unexpected files in target
  - Hash verification (spot check or full)
- **Outputs**: Comparison report
- **Tests**: Create test inventories with mismatches

#### Task 6.2: Implement Komga API Client
- **Objective**: Create `src/integrations/komga.py`
- **Inputs**: Komga URL and API key from config
- **Tools**: `requests`
- **Operations**:
  - Trigger library scan: `POST /api/v1/libraries/{id}/scan`
  - Get series list: `GET /api/v1/series`
  - Get series details: `GET /api/v1/series/{id}`
- **Outputs**: API responses
- **Tests**: Mock Komga API, test authentication

#### Task 6.3: Implement Komga Validation
- **Objective**: Verify Komga recognizes new structure
- **Inputs**: Komga API client, expected series list
- **Process**:
  1. Trigger scan for each library (Comics, Manga, H-Manga)
  2. Wait for scan completion (poll status)
  3. Query series count
  4. Compare with expected count from mapping table
  5. Spot-check 10 random series for correct metadata
- **Outputs**: Validation report with pass/fail
- **Tests**: Mock Komga responses, verify validation logic

#### Task 6.4: Implement Mylar3 API Client (Optional)
- **Objective**: Create `src/integrations/mylar3.py`
- **Inputs**: Mylar3 URL and API key from config
- **Tools**: `requests`
- **Operations**:
  - Get comic list: `GET /api?cmd=getComicList`
  - Get comic details: `GET /api?cmd=getComic&id={id}`
  - Update comic location: `POST /api?cmd=updateComic&id={id}&path={new_path}`
- **Outputs**: API responses
- **Tests**: Mock Mylar3 API

#### Task 6.5: Implement Mylar3 Validation (Optional)
- **Objective**: Verify Mylar3 compatibility
- **Inputs**: Mylar3 API client, mapping table
- **Process**:
  1. Query Mylar3 for all series
  2. For each series, check if new path exists
  3. Report any series with missing paths
  4. Optionally update Mylar3 database with new paths
- **Outputs**: Validation report
- **Tests**: Mock Mylar3 responses

#### Task 6.6: Implement Corruption Check
- **Objective**: Verify no archives were corrupted during copy
- **Inputs**: Post-migration file list
- **Tools**: `zipfile.testzip()`, `py7zr.test()`, `rarfile.testrar()`
- **Process**: Open each archive, test integrity
- **Outputs**: List of corrupted archives (should be empty)
- **Tests**: Create intentionally corrupted archive, verify detection

#### Task 6.7: Generate Validation Report
- **Objective**: Consolidate all validation results
- **File**: `output/reports/validation_{timestamp}.txt`
- **Contents**:
  - Inventory comparison results
  - Komga validation results
  - Mylar3 validation results (if applicable)
  - Corruption check results
  - Overall pass/fail status
- **Tests**: Generate sample report

#### Task 6.8: CLI for Phase 6
- **Objective**: Create `src/cli/validate.py` with commands:
  - `validate inventory --pre <json> --post <json>`
  - `validate komga --library <id>`
  - `validate mylar3`
  - `validate corruption --path <target_root>`
  - `validate all` (run all checks)
- **Inputs**: Inventories, config
- **Outputs**: Validation reports
- **Tests**: End-to-end validation

---

### Phase 7 – Rollback & Cleanup

**Objective**: Provide mechanism to revert migration if issues found, safe cleanup of old files.

#### Task 7.1: Implement Rollback Plan
- **Objective**: Create `scripts/rollback.py`
- **Inputs**: Pre-migration inventory, ledger
- **Process**:
  1. Verify backup/original files still exist
  2. Delete copied files in target directories (use ledger to identify)
  3. Optionally restore from backup if files were moved (not copied)
  4. Reset Komga/Mylar3 library paths to original
- **Safety**: Require explicit confirmation flag `--confirm-rollback`
- **Outputs**: Restored original state, rollback log
- **Tests**: Test rollback on sample migration

#### Task 7.2: Implement Cleanup Strategy
- **Objective**: Define when it's safe to delete originals
- **Conditions**:
  - Post-migration inventory verified
  - Komga/Mylar3 validation passed
  - Corruption check passed
  - User manually confirms after reviewing reports
  - Backup exists (if configured)
- **Document**: `docs/cleanup_guide.md`
- **Tests**: N/A (documentation)

#### Task 7.3: Implement Archive Old Files Script
- **Objective**: Create `scripts/archive_originals.py`
- **Inputs**: Original source paths, archive destination
- **Process**:
  1. Verify all files accounted for in post-migration inventory
  2. Move (not delete) originals to archive location: `/backup/original_comics_{timestamp}/`
  3. Preserve directory structure
  4. Create archive inventory
- **Outputs**: Archived files, archive inventory
- **Tests**: Test archival, verify structure preservation

#### Task 7.4: Implement Selective Cleanup
- **Objective**: Allow cleanup by confidence level
- **Inputs**: Confidence level filter (e.g., "delete only high confidence originals")
- **Process**: Based on ledger, delete only originals where confidence level matches filter
- **Outputs**: Deleted files list, remaining originals report
- **Tests**: Verify selective deletion

#### Task 7.5: Implement Cleanup Verification
- **Objective**: Before deletion, verify target files
- **Inputs**: Files to be deleted, post-migration inventory
- **Checks**:
  - Target file exists
  - Target file hash matches original
  - Target file not corrupted
- **Outputs**: Safe-to-delete list
- **Tests**: Verify checks prevent accidental deletion

#### Task 7.6: CLI for Phase 7
- **Objective**: Create CLI commands in main script or separate
- **Commands**:
  - `rollback execute --confirm-rollback`
  - `cleanup archive --source <path> --archive <path>`
  - `cleanup delete --confidence <level> --confirm-delete`
  - `cleanup verify --target <path>`
- **Inputs**: Config, inventories, ledger
- **Outputs**: Cleaned/archived files, logs
- **Tests**: End-to-end cleanup simulation

---

## Additional Design Specifications

### Content Type Detection Strategy

**Auto-Detection Logic** (to be implemented in `src/operations/scanner.py`):

1. Check directory name patterns:
   - `/Comics/`, `/Western/` → western
   - `/Manga/` (not H-Manga) → manga
   - `/H-Manga/`, `/Hentai/`, `/Doujin/` → hentai

2. Check ComicInfo.xml if exists:
   - `<Manga>Yes</Manga>` → manga or hentai (further detection needed)
   - Tags like `<Genre>Hentai</Genre>` → hentai
   - Publisher in known Western publishers list → western

3. Filename patterns:
   - `[CircleName]` prefix → likely hentai
   - `vNN` or `cNNN` suffix → likely manga
   - `#NNN` with publisher → likely western

4. Manual override:
   - Config file can specify: `content_type_overrides: {"/path/to/dir": "manga"}`

### LANraragi Configuration Strategy

**Detection**: On script startup, attempt connection to LANraragi URL from config.

**If Available**:
- Log: "LANraragi connected successfully"
- Enable high-confidence hentai metadata enrichment
- Cache LANraragi archive list for quick lookups

**If Unavailable**:
- Log: "LANraragi not available, using filename parsing fallback for hentai metadata"
- Set confidence ceiling to medium for all hentai items
- Continue processing with reduced metadata quality

**Configuration**:
```yaml
metadata_sources:
  lanraragi:
    enabled: true
    url: "http://localhost:3000"
    api_key: "your_api_key_here"
    timeout: 10
    required: false  # If true, script exits if LANraragi unavailable
```

### Manual Override Mechanism

**File**: `config/manual_overrides.yml`

**Format**:
```yaml
overrides:
  - source_path: "/source/comics/unknown_batman.cbz"
    target_path: "/media/Comics/DC/Batman (1940)/Batman (1940) #075.cbz"
    metadata:
      series: "Batman"
      number: "75"
      year: "1950"
    confidence: "high"
    reason: "Manually verified issue number"
```

**Processing**: During mapping phase, check for manual overrides and apply them, logging the override source.

### Parallelization Strategy

**Thread Safety Considerations**:
- Metadata API calls: Parallelizable (use thread pool)
- File operations: Serialize writes to same directory, parallelize across directories
- Hashing: CPU-bound, use process pool

**Implementation** (optional Phase 5 enhancement):
- Use `concurrent.futures.ThreadPoolExecutor` for API calls (max 5 workers to respect rate limits)
- Use `concurrent.futures.ProcessPoolExecutor` for hashing (max CPU count - 1)
- Use `multiprocessing.Queue` for ledger updates (single writer process)

**Configuration**:
```yaml
performance:
  max_api_workers: 5
  max_hash_workers: 4
  max_copy_workers: 2
```

---

## Testing Strategy

### Unit Tests
- All parsers (filename, ComicInfo.xml)
- All mappers (western, manga, hentai)
- Confidence assignment logic
- Config validation
- Hashing utility

### Integration Tests
- End-to-end enrichment with mocked APIs
- End-to-end migration with temporary directories
- Rollback functionality

### Test Fixtures
- Sample ComicInfo.xml files (valid and invalid)
- Sample filenames covering all patterns
- Sample archive files (CBZ, CBR, CB7) with known content
- Mock API responses for each provider

### Test Data
- Create `tests/fixtures/` with:
  - `sample_western.cbz` (with ComicInfo.xml)
  - `sample_manga.cbz` (without metadata)
  - `sample_hentai.cbz` (with LANraragi tags)
  - Various malformed filenames

---

## Error Recovery & Resume Capability

### Checkpoint System

**Ledger-Based Resume**:
- Each ledger entry has status: `pending`, `success`, `failed`, `skipped`
- On script startup, check for existing ledger
- Prompt user: "Previous run detected. Resume from last checkpoint? [Y/n]"
- If yes: Load ledger, filter to `pending` items only
- If no: Archive old ledger, start fresh

**Interrupt Handling**:
- Catch `KeyboardInterrupt` (Ctrl+C)
- Flush ledger to disk
- Log: "Interrupted. Run with --resume to continue."
- Exit gracefully

### Transient Error Retry

**Retry Logic** (in metadata providers):
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RequestException, Timeout))
)
def fetch_metadata(query):
    # API call here
    pass
```

**Persistent Error Handling**:
- After max retries, mark as failed in ledger
- Log full error details
- Continue with next item (don't block entire process)

---

## Security & Credentials Management

### API Key Storage

**DO NOT hardcode in config files committed to git**

**Recommended Approach**:
1. Store in environment variables: `COMICVINE_API_KEY`, `LANRARAGI_API_KEY`
2. Use `.env` file (excluded from git via `.gitignore`)
3. Load with `python-dotenv` library

**Config Template**:
```yaml
metadata_sources:
  comicvine:
    api_key: "${COMICVINE_API_KEY}"  # Loaded from environment
```

### File Permission Handling

**On file creation**:
- Preserve original permissions when copying
- On Unraid/Linux: Ensure files are readable by Komga/Mylar3 user
- Config option: `operations.set_permissions: "0644"` (if needed)

---

## Documentation Deliverables

### README.md (Project Root)

**Sections**:
1. Overview: What this project does
2. Quick Start: Installation and first run
3. Prerequisites: Python version, system requirements
4. Configuration: How to set up config files
5. Usage: Command examples for each phase
6. Troubleshooting: Link to detailed docs
7. Contributing: For future developers
8. License

### docs/metadata_strategy.md

**Sections**:
1. Overview of metadata sources
2. ComicInfo.xml standard and extensions
3. Provider-specific notes (ComicVine, AniList, LANraragi)
4. Fallback strategies
5. Field mapping tables (API field → ComicInfo field)

### docs/confidence_levels.md

**Sections**:
1. Confidence level definitions
2. Assignment criteria with examples
3. Workflow for reviewing best-guess items
4. How to use manual overrides

### docs/troubleshooting.md

**Common Issues**:
- "LANraragi connection failed"
- "API rate limit exceeded"
- "Corrupted archive detected"
- "Insufficient disk space"
- "Permission denied writing to target"
- Each with cause and solution

---

## Acceptance Criteria Summary

### Functional Criteria
✅ All phases complete without errors in dry-run mode
✅ High-confidence items migrated to correct locations
✅ Medium-confidence items flagged and optionally separated
✅ Low-confidence items moved to `_unsorted` with complete logs
✅ ComicInfo.xml present and valid in all migrated archives
✅ Komga libraries recognize and correctly parse all series
✅ Mylar3 compatible with new structure (if applicable)

### Safety Criteria
✅ No original files deleted without explicit user confirmation
✅ All destructive operations require `--confirm` flag
✅ Pre- and post-migration inventories match (accounting for unsorted)
✅ Rollback capability tested and functional
✅ Corruption checks pass for all copied files

### Quality Criteria
✅ Confidence level reports are accurate and actionable
✅ Ledger is complete and machine-readable
✅ All errors logged with sufficient context for debugging
✅ Documentation is complete and clear

### Performance Criteria (Nice to Have)
⚡ Migration of 10,000 files completes in < 24 hours (depends on hardware)
⚡ Memory usage stays under 2GB even with large collections
⚡ API rate limits respected (no bans)

---

## Implementation Timeline Estimate

**Phase 0**: 1-2 days (project setup, core infrastructure)
**Phase 1**: 1 day (inventory and hashing)
**Phase 2**: 3-5 days (metadata providers, enrichment logic)
**Phase 3**: 2 days (mapping logic, conflict detection)
**Phase 4**: 1 day (reporting)
**Phase 5**: 2-3 days (migration execution, safety checks)
**Phase 6**: 2 days (validation, integration testing)
**Phase 7**: 1 day (rollback, cleanup)

**Testing & Documentation**: 2-3 days
**Buffer for issues**: 2-3 days

**Total**: ~15-20 days of development time
