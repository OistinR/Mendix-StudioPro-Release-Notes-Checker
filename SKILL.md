---
name: release-notes-check
description: Search Mendix release notes (versions 9, 10, 11) using semantic search
argument-hint: <version1,version2,...> [optional query]
allowed-tools: [Bash, Read, Write, Grep]
user-invocable: true
---

# Mendix Release Notes Search

This skill searches Mendix release notes for versions 9, 10, and 11 using semantic search powered by a local vector database (ChromaDB).

## Usage

```
/release-notes-check 10,11
/release-notes-check 10 XPath query issue
/release-notes-check --update
/release-notes-check --rebuild
```

## How It Works

1. **Parse arguments**: Extract versions and optional query from user input
2. **Check database**: Ensure ChromaDB is initialized (auto-initialize if needed)
3. **Update if requested**: Run incremental update to fetch new releases
4. **Execute query**: Search the vector database using semantic search
5. **Format results**: Return top 5 most relevant release note chunks with version, URL, and content

## Commands to Execute

When the user invokes this skill, follow these steps:

### 1. Navigate to skill directory
```bash
cd "$CLAUDE_PROJECT_DIR/.claude/skills/release-notes-check/scripts"
```

### 2. Check if virtual environment exists, create if needed
```bash
if [ ! -d "../venv" ]; then
  echo "Creating Python virtual environment..."
  python -m venv ../venv
fi
```

### 3. Activate virtual environment
```bash
# On Windows (Git Bash)
source ../venv/Scripts/activate 2>/dev/null || . ../venv/Scripts/activate

# On Linux/Mac
source ../venv/bin/activate 2>/dev/null || true
```

### 4. Install dependencies if needed
```bash
pip install -q -r requirements.txt
```

### 5. Parse user arguments

Extract from the skill arguments:
- **Versions**: Comma-separated version numbers (e.g., "10,11" or "9")
- **Query**: Natural language search query
- **Flags**: --update or --rebuild

### 6. Execute the appropriate command

**For --rebuild flag:**
```bash
python main.py --rebuild
```

**For --update flag:**
```bash
python main.py --update
```

**For query (default):**
```bash
python main.py --query "$QUERY" --versions "$VERSIONS" --top-k 5
```

**Check if database exists (auto-initialize):**
If the database doesn't exist and user didn't specify --rebuild, automatically run:
```bash
python main.py --rebuild
```

### 7. Parse and format output

Present results to the user in a clear format:

```
🔍 Search Results for: "[query]"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 📦 Mendix 10.6.0 - Fixes
   🔗 https://docs.mendix.com/releasenotes/studio-pro/10/10.6/
   📊 Relevance: 0.87

   [Content excerpt...]

2. 📦 Mendix 10.5.0 - New Features
   🔗 https://docs.mendix.com/releasenotes/studio-pro/10/10.5/
   📊 Relevance: 0.82

   [Content excerpt...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

- **Database doesn't exist**: Automatically run `--rebuild` with user confirmation
- **Scraping fails**: Report which URLs failed and continue with others
- **No results**: Suggest broadening the search or trying different keywords
- **Network errors**: Display clear error message with retry suggestions
- **Python dependency errors**: Show installation command

## Output Format

For each result, present:
- **Version**: Full Mendix version (e.g., "10.6.0")
- **Section**: Section of the release notes (e.g., "Fixes", "New Features")
- **URL**: Direct link to the release notes page
- **Relevance**: Similarity score (0.0 - 1.0)
- **Content**: Relevant excerpt (first ~300 characters)

## Tips for Users

- Use natural language queries (e.g., "XPath query returns wrong results")
- Specify versions to narrow search (e.g., `/release-notes-check 10,11 data grid issue`)
- Run `/release-notes-check --update` periodically to fetch new releases
- If results aren't relevant, try rephrasing your query

## Technical Details

- **Vector DB**: ChromaDB (local, embedded)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Scraping**: BeautifulSoup + requests
- **Chunking**: By section (500-3000 characters)
- **Search**: Cosine similarity on semantic embeddings
