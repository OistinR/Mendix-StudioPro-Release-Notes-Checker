"""
Web scraper for Mendix release notes.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import config


class MendixReleaseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with retry logic."""
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Error fetching {url} (attempt {attempt + 1}/{config.MAX_RETRIES}): {e}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
        return None

    def extract_release_links(self, html: str, base_url: str) -> List[str]:
        """Extract links to individual release notes from index page."""
        soup = BeautifulSoup(html, 'lxml')
        links = []

        # Extract major version from base_url (e.g., "10" from ".../studio-pro/10/")
        version_match = re.search(r'/(\d+)/?$', base_url)
        if not version_match:
            return links
        major_version = version_match.group(1)

        # Find all links matching the pattern /releasenotes/studio-pro/{major}.{minor}/
        pattern = rf'/releasenotes/studio-pro/{major_version}\.\d+/?'

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Check if href matches our version pattern
            if re.search(pattern, href):
                full_url = urljoin('https://docs.mendix.com', href)
                links.append(full_url)

        return list(set(links))  # Remove duplicates

    def extract_release_content(self, html: str, url: str) -> Dict:
        """Extract content from a release notes page."""
        soup = BeautifulSoup(html, 'lxml')

        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Release"

        # Extract version from URL or title
        version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', url)
        version = version_match.group(1) if version_match else "Unknown"

        # Extract release date (if available)
        date = None
        date_patterns = [
            r'(\w+ \d+,? \d{4})',  # e.g., "March 15, 2023" or "March 15 2023"
            r'(\d{4}-\d{2}-\d{2})'  # e.g., "2023-03-15"
        ]
        for pattern in date_patterns:
            date_match = re.search(pattern, html)
            if date_match:
                date = date_match.group(1)
                break

        # Extract main content
        # Try to find the main content area
        main_content = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
        if not main_content:
            main_content = soup.find('body')

        # Extract sections
        sections = []
        if main_content:
            # Look for headings and their content
            for heading in main_content.find_all(['h2', 'h3']):
                section_title = heading.get_text(strip=True)
                section_content = []

                # Collect content until next heading
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3']:
                        break
                    text = sibling.get_text(strip=True)
                    if text:
                        section_content.append(text)

                if section_content:
                    sections.append({
                        'title': section_title,
                        'content': '\n'.join(section_content)
                    })

        # If no sections found, just grab all text
        if not sections:
            full_text = main_content.get_text(separator='\n', strip=True) if main_content else ""
            sections = [{'title': 'Content', 'content': full_text}]

        return {
            'version': version,
            'title': title,
            'date': date,
            'url': url,
            'sections': sections
        }

    def scrape_version(self, version: str) -> List[Dict]:
        """Scrape all release notes for a specific version."""
        base_url = config.RELEASE_NOTES_URLS.get(version)
        if not base_url:
            print(f"Unknown version: {version}")
            return []

        print(f"Scraping Mendix {version} release notes...")

        # Fetch index page
        html = self.fetch_page(base_url)
        if not html:
            print(f"Failed to fetch index page for version {version}")
            return []

        # Extract release links
        release_links = self.extract_release_links(html, base_url)
        print(f"Found {len(release_links)} releases for version {version}")

        # Scrape each release
        releases = []
        for i, link in enumerate(release_links, 1):
            print(f"Scraping {i}/{len(release_links)}: {link}")

            html = self.fetch_page(link)
            if html:
                release_data = self.extract_release_content(html, link)
                releases.append(release_data)

                # Be respectful with delays
                if i < len(release_links):
                    time.sleep(config.REQUEST_DELAY)
            else:
                print(f"Failed to fetch: {link}")

        return releases


def scrape_all_versions() -> List[Dict]:
    """Scrape release notes for all configured versions."""
    scraper = MendixReleaseScraper()
    all_releases = []

    for version in config.RELEASE_NOTES_URLS.keys():
        releases = scraper.scrape_version(version)
        all_releases.extend(releases)

    print(f"\nTotal releases scraped: {len(all_releases)}")
    return all_releases


if __name__ == '__main__':
    # Test the scraper
    import json
    releases = scrape_all_versions()
    print(json.dumps(releases[:2], indent=2))  # Print first 2 for preview
