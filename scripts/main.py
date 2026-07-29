#!/usr/bin/env python3
"""
Main entry point for Mendix release notes search tool.
"""

import argparse
import sys
from scraper import scrape_all_versions
from indexer import build_index, update_index
from query import search


def main():
    parser = argparse.ArgumentParser(
        description='Mendix Release Notes Search Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build the database for the first time
  python main.py --rebuild

  # Update the database with new releases
  python main.py --update

  # Search for XPath issues
  python main.py --query "XPath query issues"

  # Search only in version 10 and 11
  python main.py --query "data grid sorting" --versions 10,11

  # Get more results
  python main.py --query "performance issues" --top-k 10
        """
    )

    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Full rebuild of database (scrapes all release notes)'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Incremental update (only scrapes new/changed releases)'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Search query (natural language)'
    )
    parser.add_argument(
        '--versions',
        type=str,
        help='Comma-separated major versions to filter (e.g., "10,11")'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of results to return (default: 5)'
    )

    args = parser.parse_args()

    try:
        if args.rebuild:
            print("[*] Rebuilding database from scratch...")
            print("This may take several minutes...\n")
            docs = scrape_all_versions()
            if docs:
                build_index(docs)
                print("\n[OK] Database rebuilt successfully")
            else:
                print("\n[ERROR] No documents were scraped")
                sys.exit(1)

        elif args.update:
            print("[*] Checking for updates...")
            update_index()
            print("[OK] Database updated")

        elif args.query:
            versions = args.versions.split(',') if args.versions else None
            if versions:
                print(f"Searching in versions: {', '.join(versions)}")

            results = search(args.query, versions=versions, top_k=args.top_k)

            if results:
                print(f"\nFound {len(results)} results for: \"{args.query}\"\n")
                print("=" * 80)

                for i, result in enumerate(results, 1):
                    print(f"\n{i}. Version {result['metadata']['version']}")
                    print(f"   Section: {result['metadata']['section']}")
                    print(f"   URL: {result['metadata']['url']}")
                    print(f"   Relevance: {result['score']:.3f}")
                    print(f"\n   {result['content'][:300]}...")
                    print("-" * 80)
            else:
                print(f"\nNo results found for: \"{args.query}\"")
                print("\nTry:")
                print("  - Broadening your search terms")
                print("  - Removing version filters")
                print("  - Using different keywords")

        else:
            parser.print_help()
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
