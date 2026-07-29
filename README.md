# 🔍 Mendix Studio Pro Release Notes Checker

A semantic search tool for Mendix Studio Pro release notes. Query release notes from versions 9, 10, and 11 using natural language to quickly find bug fixes, features, and known issues.

> **"Has this Mendix bug or behavior already been documented or fixed?"**

## What It Does

This tool scrapes Mendix Studio Pro release notes, indexes them in a local vector database (LanceDB), and enables semantic search using natural language queries. Perfect for:

- 🐛 Finding if a bug has been fixed
- 📋 Checking when a feature was introduced
- 🔍 Discovering related known issues
- 📊 Exploring release history across versions

## ✨ Features

- 🔎 **Semantic search** - Find relevant release notes using natural language
- 📦 **Multi-version support** - Search across Mendix 9, 10, and 11
- 🚀 **Fast queries** - Local LanceDB with precomputed embeddings
- 🔄 **Incremental updates** - Only scrape new/changed releases
- 🎯 **Version filtering** - Search specific versions only
- 🏠 **Fully offline** - All embeddings generated locally (no API calls)

## 📋 Prerequisites

- Python 3.8+
- Internet connection (only needed for scraping, not for querying)
- ~200MB disk space for the vector database

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/OistinR/Mendix-StudioPro-Release-Notes-Checker.git
cd Mendix-StudioPro-Release-Notes-Checker
```

### 2. Set Up Python Environment

Create and activate a virtual environment:

```bash
# Windows (Git Bash)
python -m venv venv
source venv/Scripts/activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
cd scripts
pip install -r requirements.txt
```

### 3. Build the Database (First Time)

Scrape all release notes and build the vector database:

```bash
python main.py --rebuild
```

This takes **5-10 minutes** and only needs to be done once (or when you want a full refresh).

### 4. Search Release Notes

```bash
# Basic search
python main.py --query "XPath query returns wrong results"

# Search specific versions
python main.py --query "data grid sorting issue" --versions 10,11

# Get more results
python main.py --query "performance problems" --top-k 10
```

### 5. Update the Database (Periodically)

Check for new releases and update incrementally:

```bash
python main.py --update
```

This is **fast** (10-30 seconds) and only scrapes new/changed pages.

## 🎯 Usage as a Claude Code Skill

If you're using this as a Claude Code skill, invoke it from any conversation:

```
/release-notes-check XPath issue in version 10
/release-notes-check 10,11 data grid performance
/release-notes-check --update
```

Claude Code will automatically handle setup and formatting.

---

## 📁 Project Structure

```
Mendix-StudioPro-Release-Notes-Checker/
├── README.md                   # This file
├── SKILL.md                    # Claude Code skill definition (optional)
├── scripts/
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # CLI entry point
│   ├── scraper.py             # Web scraping logic
│   ├── indexer.py             # Vector database indexing
│   ├── query.py               # Semantic search
│   └── config.py              # Configuration
├── db/                         # LanceDB database (auto-created)
│   ├── mendix_release_notes.lance/  # Vector store
│   └── metadata.json          # Change tracking for incremental updates
└── venv/                       # Python virtual environment (you create this)
```

---

## ⚙️ How It Works

### Architecture

```
Mendix Docs Website
    ↓ (scraper.py)
Release Notes HTML
    ↓ (indexer.py)
Chunked Sections (by heading)
    ↓ (sentence-transformers)
Vector Embeddings (384-dimensional)
    ↓ (LanceDB)
Local Vector Database
    ↓ (query.py)
Semantic Search Results
```

### Key Components

1. **Scraper** (`scraper.py`):
   - Fetches release notes from Mendix documentation
   - Extracts version numbers, dates, sections, and content
   - Handles retries and rate limiting gracefully

2. **Indexer** (`indexer.py`):
   - Chunks content by section headings (500-3000 characters)
   - Generates embeddings using `all-MiniLM-L6-v2` (384 dimensions)
   - Stores in LanceDB with metadata (version, URL, section, date)
   - Tracks content hashes for incremental updates

3. **Query Engine** (`query.py`):
   - Converts user query to embedding vector
   - Searches LanceDB using cosine similarity
   - Filters by version(s) if specified
   - Returns top-k ranked results

4. **Main CLI** (`main.py`):
   - Command-line interface for all operations
   - Orchestrates scraping, indexing, and querying
   - Error handling and progress feedback

---

## 🔧 Configuration

Edit `scripts/config.py` to customize:

```python
# Release notes URLs
RELEASE_NOTES_URLS = {
    "9": "https://docs.mendix.com/releasenotes/studio-pro/9/",
    "10": "https://docs.mendix.com/releasenotes/studio-pro/10/",
    "11": "https://docs.mendix.com/releasenotes/studio-pro/11/",
}

# Embedding model (change for better quality)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Chunking settings
MAX_CHUNK_SIZE = 3000  # characters
TARGET_CHUNK_SIZE = 2000
```

---

## 🧪 Examples

### Example 1: Finding XPath Issues

```bash
$ python main.py --query "XPath returns wrong results"

Found 5 results for: "XPath returns wrong results"

1. Version 10.6.0
   Section: Fixes
   URL: https://docs.mendix.com/releasenotes/studio-pro/10/10.6/
   Relevance: 0.873

   Fixed an issue where XPath queries returned incorrect results
   when using complex predicates with nested attributes...
```

### Example 2: Version-Specific Search

```bash
$ python main.py --query "data grid sorting" --versions 11

Searching in versions: 11

Found 3 results for: "data grid sorting"
...
```

### Example 3: Broad Search

```bash
$ python main.py --query "performance improvements" --top-k 10

Found 10 results for: "performance improvements"
...
```

---

## 🔄 Updating the Database

### Incremental Update (Recommended)

```bash
python main.py --update
```

- Checks for new or modified release notes
- Only scrapes changed pages
- Fast (usually < 30 seconds)

### Full Rebuild

```bash
python main.py --rebuild
```

- Scrapes all release notes from scratch
- Rebuilds entire database
- Slow (~5-10 minutes)
- Use when: switching models, fixing scraping issues, or major version updates

---

## 🎓 Learning Vector Databases

This project is a great way to learn about vector databases! Key concepts:

### 1. **Vector Embeddings**
Text is converted to dense vectors (384 dimensions) that capture semantic meaning:
```python
"XPath query issue" → [0.12, -0.34, 0.56, ..., 0.78]
```

### 2. **Semantic Search**
Similar meanings = similar vectors (measured by cosine similarity):
```python
similarity("bug fix", "defect resolved") > similarity("bug fix", "new feature")
```

### 3. **Chunking Strategy**
Documents are split into chunks for better precision:
- ✅ Small chunks = precise results
- ❌ Too small = loss of context
- Target: 500-3000 characters per chunk

### 4. **Metadata Filtering**
Combine vector search with structured filters:
```python
search("performance") WHERE version IN ("10", "11")
```

### 5. **Incremental Indexing**
Track changes to avoid re-processing unchanged documents:
- Hash each document
- Compare with stored hashes
- Only re-index changed documents

---

## 🐛 Troubleshooting

### Database Not Found

```bash
❌ Error: Database not found

Solution:
python main.py --rebuild
```

### No Results

```
No results found for: "your query"

Try:
  - Broadening your search terms
  - Removing version filters
  - Using different keywords
```

### Slow First Query

The first query loads the embedding model (~90MB) into memory. Subsequent queries are fast.

### Scraping Errors

If scraping fails:
1. Check internet connection
2. Verify Mendix docs site is accessible
3. Try again (may be temporary)

### Python Environment Issues

```bash
# Recreate virtual environment
rm -rf ../venv
python -m venv ../venv
source ../venv/Scripts/activate
pip install -r requirements.txt
```

---

## 📊 Performance

- **Initial scraping**: 5-10 minutes (one-time)
- **Incremental update**: 10-30 seconds
- **Query time**: 100-500ms
- **Database size**: ~200MB (all versions)
- **Memory usage**: ~500MB (model loaded)

---

## 🚀 Future Enhancements

- [ ] Add more Mendix documentation (best practices, how-tos)
- [ ] Hybrid search (combine semantic + keyword)
- [ ] Export results to markdown
- [ ] Web UI for non-technical users
- [ ] Scheduled auto-updates (cron job)
- [ ] Support for Mendix 8 and 12

---

## 🙋 FAQ

**Q: Do I need an API key?**  
A: No! Everything runs locally. No OpenAI, Anthropic, or other API keys needed.

**Q: How accurate is the semantic search?**  
A: The `all-MiniLM-L6-v2` model is fast and good for general queries. For higher accuracy, you can switch to a larger model in `config.py`.

**Q: Can I add more documentation sources?**  
A: Yes! Edit `config.py` to add URLs for other Mendix documentation (e.g., platform release notes, best practices).

**Q: How often should I update?**  
A: Run `--update` monthly or when you know a new version was released.

**Q: What if I get no results?**  
A: Try broader keywords, remove version filters, or rephrase your query.

---

## 🤝 Contributing

Found a bug or have an idea? Open an issue or submit a pull request!

---

## 📄 License

MIT License - feel free to use and modify.

---

**Built to make Mendix development easier! 🚀**
