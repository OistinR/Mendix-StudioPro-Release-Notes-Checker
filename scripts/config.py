"""
Configuration for Mendix release notes scraper.
"""

# Base URLs for Mendix release notes by version
RELEASE_NOTES_URLS = {
    "9": "https://docs.mendix.com/releasenotes/studio-pro/9/",
    "10": "https://docs.mendix.com/releasenotes/studio-pro/10/",
    "11": "https://docs.mendix.com/releasenotes/studio-pro/11/",
}

# ChromaDB settings
CHROMA_DB_PATH = "../db"
COLLECTION_NAME = "mendix_release_notes"

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Scraping settings
REQUEST_DELAY = 0.5  # seconds between requests
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Chunking settings
MAX_CHUNK_SIZE = 3000  # characters
TARGET_CHUNK_SIZE = 2000  # characters
