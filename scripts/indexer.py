"""
Indexer for storing release notes in LanceDB with embeddings.
"""

import lancedb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import hashlib
import json
import os
from datetime import datetime
import config


class ReleaseNotesIndexer:
    def __init__(self):
        # Initialize LanceDB
        db_path = os.path.join(os.path.dirname(__file__), config.CHROMA_DB_PATH)
        os.makedirs(db_path, exist_ok=True)

        self.db = lancedb.connect(db_path)

        # Initialize embedding model
        print(f"Loading embedding model: {config.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        print("Embedding model loaded successfully")

        # Metadata file path
        self.metadata_path = os.path.join(db_path, 'metadata.json')

    def chunk_section(self, section_content: str) -> List[str]:
        """Split section content into smaller chunks if needed."""
        if len(section_content) <= config.MAX_CHUNK_SIZE:
            return [section_content]

        chunks = []
        paragraphs = section_content.split('\n')
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            para_length = len(paragraph)

            if current_length + para_length > config.TARGET_CHUNK_SIZE and current_chunk:
                # Save current chunk and start new one
                chunks.append('\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = para_length
            else:
                current_chunk.append(paragraph)
                current_length += para_length

        # Add remaining content
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def index_releases(self, releases: List[Dict]):
        """Index releases into LanceDB."""
        print(f"Indexing {len(releases)} releases...")

        records = []

        for release in releases:
            version = release['version']
            title = release['title']
            date = release.get('date', 'Unknown')
            url = release['url']

            for section in release['sections']:
                section_title = section['title']
                section_content = section['content']

                # Chunk the section if needed
                chunks = self.chunk_section(section_content)

                for chunk_idx, chunk in enumerate(chunks):
                    records.append({
                        'text': chunk,
                        'version': version,
                        'major_version': version.split('.')[0],
                        'title': title,
                        'release_date': date,
                        'url': url,
                        'section': section_title,
                        'chunk_index': chunk_idx
                    })

        # Generate embeddings
        print(f"Generating embeddings for {len(records)} chunks...")
        texts = [r['text'] for r in records]
        embeddings = self.model.encode(texts, show_progress_bar=True)

        # Add embeddings to records
        for i, record in enumerate(records):
            record['vector'] = embeddings[i].tolist()

        # Create or overwrite table
        print("Adding documents to LanceDB...")
        try:
            self.db.create_table(
                config.COLLECTION_NAME,
                data=records,
                mode="overwrite"
            )
        except Exception as e:
            print(f"Error creating table: {e}")
            # If table exists, drop and recreate
            try:
                self.db.drop_table(config.COLLECTION_NAME)
                self.db.create_table(
                    config.COLLECTION_NAME,
                    data=records,
                    mode="create"
                )
            except:
                pass

        print(f"[OK] Indexed {len(records)} chunks successfully")

        # Update metadata file
        self.save_metadata(releases)

    def save_metadata(self, releases: List[Dict]):
        """Save metadata for change detection."""
        metadata = {
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'release_hashes': {}
        }

        for release in releases:
            url = release['url']
            content_hash = hashlib.md5(json.dumps(release).encode()).hexdigest()
            metadata['release_hashes'][url] = content_hash

        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def load_metadata(self) -> Dict:
        """Load metadata from file."""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        return {}

    def get_collection_stats(self):
        """Get statistics about the collection."""
        try:
            table = self.db.open_table(config.COLLECTION_NAME)
            count = len(table.to_pandas())
            return {
                'total_chunks': count,
                'collection_name': config.COLLECTION_NAME
            }
        except:
            return {
                'total_chunks': 0,
                'collection_name': config.COLLECTION_NAME
            }


def build_index(releases: List[Dict]):
    """Build the index from scratch."""
    indexer = ReleaseNotesIndexer()
    indexer.index_releases(releases)

    stats = indexer.get_collection_stats()
    print(f"\nIndex statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")


def update_index():
    """Update the index with new/changed releases."""
    from scraper import scrape_all_versions

    indexer = ReleaseNotesIndexer()
    old_metadata = indexer.load_metadata()
    old_hashes = old_metadata.get('release_hashes', {})

    # Scrape all releases
    releases = scrape_all_versions()

    # Find new or modified releases
    new_releases = []
    for release in releases:
        url = release['url']
        content_hash = hashlib.md5(json.dumps(release).encode()).hexdigest()

        if url not in old_hashes or old_hashes[url] != content_hash:
            new_releases.append(release)

    if new_releases:
        print(f"Found {len(new_releases)} new or updated releases")
        indexer.index_releases(new_releases)
    else:
        print("No changes detected")


if __name__ == '__main__':
    # Test the indexer
    from scraper import scrape_all_versions
    releases = scrape_all_versions()
    build_index(releases)
