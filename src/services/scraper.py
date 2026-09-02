import json
import hashlib
import re
from typing import List, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from ..config import REQUEST_TIMEOUT, USER_AGENT, SAMPLE_FIXTURE_PATH
from ..models.state import SourceChunk


class ScraperService:
    """Collects, cleans, and chunks public competitor website data."""

    def __init__(self, demo_fixture_path: Optional[str] = None):
        self.fixture_path = demo_fixture_path or SAMPLE_FIXTURE_PATH
        self._demo_data = self._load_fixtures()

    def _load_fixtures(self) -> dict:
        try:
            with open(self.fixture_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"competitors": []}

    @staticmethod
    def _clean_text(html_content: str) -> str:
        """Parses HTML and extracts clean, readable text."""
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Collapse multiple spaces and newlines
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _generate_chunk_id(url: str, text: str) -> str:
        """Generates a deterministic unique hash for source tracking."""
        data = f"{url}:{text[:100]}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:12]

    @staticmethod
    def _derive_competitor_name(url: str) -> str:
        """Derives a human-readable brand name from a URL."""
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = re.sub(r"^www\.", "", domain)
        parts = domain.split(".")
        if parts:
            return parts[0].capitalize()
        return "Unknown Competitor"

    def fetch_demo_chunks(self, competitor_name: str) -> List[SourceChunk]:
        """Retrieves verified sample chunks for offline demo testing."""
        chunks: List[SourceChunk] = []
        name_lower = competitor_name.lower()
        for comp in self._demo_data.get("competitors", []):
            if comp["name"].lower() in name_lower or name_lower in comp["name"].lower():
                for page in comp.get("pages", []):
                    chunk_id = self._generate_chunk_id(page["url"], page["content"])
                    chunks.append(
                        SourceChunk(
                            chunk_id=chunk_id,
                            competitor_name=comp["name"],
                            url=page["url"],
                            title=page.get("title", ""),
                            content=page["content"],
                            content_type="pricing" if "pricing" in page["url"] else "product",
                        )
                    )
        return chunks

    def fetch_page(self, url: str, competitor_name: Optional[str] = None) -> List[SourceChunk]:
        """Fetches a URL and returns structured SourceChunks."""
        if not competitor_name:
            competitor_name = self._derive_competitor_name(url)

        headers = {"User-Agent": USER_AGENT}
        try:
            with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True, headers=headers) as client:
                response = client.get(url)
                if response.status_code == 200:
                    text = self._clean_text(response.text)
                    if len(text) > 100:
                        # Chunk into logical segments if long
                        chunk_size = 1200
                        chunks = []
                        words = text.split()
                        current_segment = []
                        current_len = 0
                        for word in words:
                            current_segment.append(word)
                            current_len += len(word) + 1
                            if current_len >= chunk_size:
                                segment_text = " ".join(current_segment)
                                chunks.append(
                                    SourceChunk(
                                        chunk_id=self._generate_chunk_id(url, segment_text),
                                        competitor_name=competitor_name,
                                        url=url,
                                        title=f"{competitor_name} Live Content",
                                        content=segment_text,
                                        content_type="webpage",
                                    )
                                )
                                current_segment = []
                                current_len = 0
                        if current_segment:
                            segment_text = " ".join(current_segment)
                            chunks.append(
                                SourceChunk(
                                    chunk_id=self._generate_chunk_id(url, segment_text),
                                    competitor_name=competitor_name,
                                    url=url,
                                    title=f"{competitor_name} Live Content",
                                    content=segment_text,
                                    content_type="webpage",
                                )
                            )
                        return chunks
        except Exception:
            pass

        # Fallback to demo fixture if live fetch fails or is blocked
        demo_chunks = self.fetch_demo_chunks(competitor_name)
        if demo_chunks:
            return demo_chunks

        # Generic fallback chunk if completely unresolvable
        return [
            SourceChunk(
                chunk_id=self._generate_chunk_id(url, "Fallback public data"),
                competitor_name=competitor_name,
                url=url,
                title=f"{competitor_name} Overview",
                content=f"Public catalog and business services profile for {competitor_name} ({url}).",
                content_type="general",
            )
        ]
