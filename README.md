# Comic Collection Migration & Normalization

A comprehensive Python tool for migrating and normalizing large digital comic collections (Western comics, manga, and hentai/doujin) into a consistent structure for use with Komga and Mylar3.

## ⚠️ Current Status: Phase 0 Complete

**Phase 0 - Project Bootstrap** has been implemented. The core infrastructure is ready for Phase 1-7 development.

### What's Implemented (Phase 0)
- ✅ Complete project structure and directory layout
- ✅ Configuration system with Pydantic validation
- ✅ Centralized JSON-structured logging
- ✅ Comprehensive safety checks (paths, permissions, disk space, Python version)
- ✅ Dry-run infrastructure for safe testing
- ✅ CLI skeleton with safety check integration
- ✅ Full documentation and coding standards

### What's Coming (Phases 1-7)
- ⏳ Phase 1: Inventory & Backup
- ⏳ Phase 2: Metadata Enrichment
- ⏳ Phase 3: Mapping Logic
- ⏳ Phase 4: Dry-Run Reporting
- ⏳ Phase 5: Migration Execution
- ⏳ Phase 6: Validation (Komga/Mylar3)
- ⏳ Phase 7: Rollback & Cleanup

## 🎯 Project Goals

1. **Safety First**: All operations default to dry-run mode
2. **Metadata-Driven**: ComicInfo.xml standards for all comics
3. **Confidence-Based**: High/medium/low confidence levels for automated decisions
4. **Reversible**: Complete rollback capability
5. **Cross-Platform**: Windows, Linux, macOS, Unraid compatible

## 📋 Prerequisites

- **Python 3.8+** (required)
- **Operating System**: Windows 10/11, Linux, macOS, or Unraid
- **Disk Space**: Sufficient space on target filesystems (100GB+ recommended)
- **Optional**: LANraragi (for hentai/doujin metadata)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd project_comic_sort
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 3. Configure Paths

```bash
# Copy example configs
cp config/example_config.yml config/config.yml
cp config/paths.example.yml config/paths.yml

# Edit config/paths.yml with your actual paths
# - Set source_libraries to your existing comic directories
# - Set target_roots to where you want organized libraries
# - Configure backup_location for safety
```

### 4. Run Safety Checks

```bash
# Test that your environment is properly configured
python -m src.cli.inventory --safety-checks-only
```

You should see output like:

```
======================================================================
SAFETY CHECK RESULTS
======================================================================

✓ PYTHON_VERSION: PASS [CRITICAL]
  Python 3.11.0 (minimum: 3.8)

✓ SOURCE_LIBRARIES_EXIST: PASS [CRITICAL]
  2/2 source libraries accessible

...

✅ ALL CRITICAL CHECKS PASSED
======================================================================
```

## 📖 Configuration

### Main Configuration (`config/config.yml`)

```yaml
environment:
  dry_run: true  # ALWAYS start in dry-run mode!
  profile: "development"

logging:
  level: "INFO"
  console_output: true

safety:
  require_backup: true
  min_free_space_bytes: 107374182400  # 100GB

# ... see config/example_config.yml for all options
```

### Paths Configuration (`config/paths.yml`)

```yaml
source_libraries:
  - path: "C:/Comics/Western"
    content_type: "western"
    enabled: true
  
  - path: "C:/Comics/Manga"
    content_type: "manga"
    enabled: true

target_roots:
  western: "C:/Media/Comics"
  manga: "C:/Media/Manga"
  hentai: "C:/Media/H-Manga"

temp_workspace: "C:/Temp/comic_migration_workspace"
backup_location: "E:/Backups/comic_migration_backup"
```

### Environment Variables

For sensitive data (API keys), use environment variables or a `.env` file:

```bash
# .env file
COMICVINE_API_KEY=your_api_key_here
LANRARAGI_URL=http://localhost:3000
LANRARAGI_API_KEY=your_api_key_here
```

## 🛠️ Usage (Phase 0)

### Run Safety Checks

```bash
python -m src.cli.inventory --safety-checks-only
```

### View Help

```bash
python -m src.cli.inventory --help
```

### Test CLI (Stubs Only - Phase 1 TODO)

```bash
# These commands show what will be available in Phase 1
python -m src.cli.inventory scan --source /path/to/comics
python -m src.cli.inventory verify --original inventory.json --backup /path
```

## 📁 Project Structure

```
project_comic_sort/
├── src/                    # Source code
│   ├── core/              # Core infrastructure (config, logging, dry-run)
│   ├── metadata/          # Metadata providers (Phase 2 - TODO)
│   ├── parsers/           # File and filename parsing (Phase 2 - TODO)
│   ├── mappers/           # Path mapping logic (Phase 3 - TODO)
│   ├── operations/        # High-level operations (safety checks implemented)
│   └── cli/               # Command-line interfaces (skeleton implemented)
├── config/                # Configuration templates
├── docs/                  # Documentation (TODO)
├── logs/                  # Runtime logs (auto-generated)
├── output/                # Generated outputs (inventories, reports, etc.)
├── tests/                 # Test suite (Phase 0 - TODO)
└── scripts/               # Utility scripts (Phase 7 - TODO)
```

## 🧪 Testing (Phase 0 - TODO)

Tests will be added in later phases:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_config.py
```

## 📚 Documentation

- **[Implementation Plan](.project-files/project_plan.md)**: Comprehensive 7-phase plan
- **Agent Instructions** (TODO): Guidelines for AI coding agents
- **Metadata Strategy** (TODO): Metadata provider details
- **Confidence Levels** (TODO): Confidence system explanation
- **Troubleshooting** (TODO): Common issues and solutions

## 🔒 Safety Features

### 1. Dry-Run Mode (Default)

ALL operations default to dry-run mode. Nothing happens to your files until you:
1. Review dry-run reports
2. Explicitly set `dry_run: false` in config
3. Re-run commands

### 2. Safety Checks

Before any operation:
- ✅ Python version verification
- ✅ Source paths exist and readable
- ✅ Target paths writable
- ✅ No dangerous path overlaps
- ✅ Sufficient disk space
- ✅ Temp workspace accessible

### 3. Comprehensive Logging

All operations logged to JSON files:
- `logs/operations_{timestamp}.log` - All operations (INFO+)
- `logs/debug_{timestamp}.log` - Verbose debug output
- `logs/errors_{timestamp}.log` - Errors only

### 4. Backup Requirements

System can require backups before destructive operations (configurable).

## 🎨 Naming Conventions

### Western Comics
```
/media/Comics/
  ├── DC/
  │   └── Batman (1940)/
  │       └── Batman (1940) #001 (1940-04-25).cbz
  └── Marvel/
      └── Amazing Spider-Man (1963)/
          └── Amazing Spider-Man (1963) #001 (1963-03-10).cbz
```

### Manga
```
/media/Manga/
  ├── One Piece/
  │   ├── One Piece v01.cbz
  │   └── One Piece v02.cbz
  └── Naruto/
      ├── Naruto v01.cbz
      └── Naruto v02.cbz
```

### Hentai/Doujin
```
/media/H-Manga/
  ├── _oneshots/
  │   └── (123456) - Title (English) [nhentai].cbz
  └── [CircleName]/
      └── Series Title/
          └── Series Title v01.cbz
```

## 🔧 Development

### Code Standards

- **Pathlib**: Always use `pathlib.Path` for path operations
- **Type Hints**: Required for all public functions
- **Docstrings**: Google format for all modules/functions
- **Line Length**: Maximum 100 characters
- **Formatting**: Use `black` for code formatting
- **Linting**: Use `pylint` for code quality

### Architecture Patterns

- **Provider Pattern**: Metadata sources inherit from `BaseMetadataProvider`
- **Factory Pattern**: Mapper selection based on content type
- **Strategy Pattern**: Confidence level assignment
- **Repository Pattern**: Inventory/ledger persistence

## 🤝 Contributing

This project is designed for AI-assisted development. See `docs/agent_instructions.md` (TODO) for guidelines.

## 📝 License

[License information to be added]

## 🙏 Acknowledgments

- **Komga**: https://komga.org/
- **Mylar3**: https://github.com/mylar3/mylar3
- **LANraragi**: https://github.com/Difegue/LANraragi
- **ComicVine**: https://comicvine.gamespot.com/
- **AniList**: https://anilist.co/

## ⚡ Roadmap

### Phase 1 (Next) - Inventory & Backup
- File scanning and discovery
- SHA256 hash calculation
- Inventory generation
- Backup verification

### Phase 2 - Metadata Enrichment
- ComicInfo.xml parsing
- API integrations (ComicVine, AniList, LANraragi)
- Confidence level assignment

### Phase 3 - Mapping Logic
- Target path calculation
- Conflict detection
- Mapping table generation

### Phase 4 - Dry-Run Reporting
- Summary reports
- Confidence breakdowns
- Conflict reports

### Phase 5 - Migration Execution
- Safe file copy operations
- Batch processing
- Progress tracking

### Phase 6 - Validation
- Inventory comparison
- Komga/Mylar3 integration
- Corruption checks

### Phase 7 - Rollback & Cleanup
- Rollback mechanism
- Safe cleanup
- Archive old files

---

**Status**: Phase 0 Complete ✅ | **Next**: Phase 1 Implementation
