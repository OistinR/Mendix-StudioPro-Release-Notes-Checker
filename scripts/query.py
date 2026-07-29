"""
Query interface for searching release notes using semantic search with LanceDB.
"""

import lancedb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import os
import config


class ReleaseNotesQuery:
    def __init__(self):
        # Initialize LanceDB
        db_path = os.path.join(os.path.dirname(__file__), config.CHROMA_DB_PATH)

        if not os.path.exists(db_path):
            raise FileNotFoundError(
                f"Database not found at {db_path}. "
                "Please run 'python main.py --rebuild' first."
            )

        self.db = lancedb.connect(db_path)

        try:
            self.table = self.db.open_table(config.COLLECTION_NAME)
        except Exception as e:
            raise FileNotFoundError(
                f"Table '{config.COLLECTION_NAME}' not found. "
                "Please run 'python main.py --rebuild' first."
            )

        # Initialize embedding model
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)

    def search(
        self,
        query: str,
        versions: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search release notes using semantic search.

        Args:
            query: Natural language search query
            versions: Filter by major versions (e.g., ["10", "11"])
            top_k: Number of results to return

        Returns:
            List of {content, metadata, score} dictionaries
        """
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]

        # Build filter if versions specified
        if versions:
            # LanceDB uses SQL-like WHERE syntax
            version_filter = " OR ".join([f"major_version = '{v}'" for v in versions])
            results = self.table.search(query_embedding).where(version_filter).limit(top_k).to_pandas()
        else:
            results = self.table.search(query_embedding).limit(top_k).to_pandas()

        # Format results
        formatted_results = []
        for idx, row in results.iterrows():
            formatted_results.append({
                'content': row['text'],
                'metadata': {
                    'version': row['version'],
                    'major_version': row['major_version'],
                    'title': row['title'],
                    'release_date': row['release_date'],
                    'url': row['url'],
                    'section': row['section'],
                    'chunk_index': str(row['chunk_index'])
                },
                'score': 1 - row['_distance'],  # Convert distance to similarity
                'id': idx
            })

        return formatted_results


def search(query: str, versions: Optional[List[str]] = None, top_k: int = 5) -> List[Dict]:
    """
    Convenience function for searching release notes.

    Args:
        query: Natural language search query
        versions: Filter by major versions (e.g., ["10", "11"])
        top_k: Number of results to return

    Returns:
        List of {content, metadata, score} dictionaries
    """
    query_engine = ReleaseNotesQuery()
    return query_engine.search(query, versions, top_k)


if __name__ == '__main__':
    # Test the query engine
    import sys

    test_query = sys.argv[1] if len(sys.argv) > 1 else "XPath query issues"
    print(f"Searching for: {test_query}\n")

    results = search(test_query, top_k=3)

    for i, result in enumerate(results, 1):
        print(f"{i}. Version {result['metadata']['version']} - {result['metadata']['section']}")
        print(f"   URL: {result['metadata']['url']}")
        print(f"   Relevance: {result['score']:.3f}")
        print(f"   {result['content'][:200]}...")
        print()
