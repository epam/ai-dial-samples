"""Direct DuckDuckGo HTML search, adapted from khshanovskyi/duckduckgo-mcp-server.

See THIRD_PARTY_NOTICES.md. No MCP runtime or API key is required.
"""

import asyncio
import time
from collections import deque
from urllib.parse import parse_qs, urlsplit

import httpx
from bs4 import BeautifulSoup


class DuckDuckGoSearch:
    def __init__(self, url: str = "https://html.duckduckgo.com/html"):
        self.url = url
        self._requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def _rate_limit(self) -> None:
        async with self._lock:
            now = time.monotonic()
            while self._requests and now - self._requests[0] >= 60:
                self._requests.popleft()
            if len(self._requests) >= 30:
                await asyncio.sleep(max(0, 60 - (now - self._requests[0])))
            self._requests.append(time.monotonic())

    async def search(self, query: str) -> dict:
        await self._rate_limit()
        try:
            async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
                response = await client.post(
                    self.url,
                    data={"q": query, "b": "", "kl": ""},
                    headers={
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml",
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError:
            return {"error": "Web search is unavailable or timed out. Do not invent results."}

        results = parse_results(response.text)
        if not results:
            return {"results": [], "notice": "No results returned. DuckDuckGo may have blocked the request or shown a bot challenge."}
        return {"results": results}


def parse_results(html: str) -> list[dict]:
    results = []
    for element in BeautifulSoup(html, "html.parser").select(".result"):
        link = element.select_one(".result__title a")
        if link is None:
            continue
        raw_url = link.get("href", "")
        parsed = urlsplit(raw_url)
        if parsed.hostname in {"duckduckgo.com", "www.duckduckgo.com"}:
            if parsed.path != "/l/":
                continue
            raw_url = parse_qs(parsed.query).get("uddg", [""])[0]
        if urlsplit(raw_url).scheme not in {"http", "https"}:
            continue
        snippet = element.select_one(".result__snippet")
        results.append({
            "title": link.get_text(" ", strip=True)[:300],
            "url": raw_url,
            "snippet": snippet.get_text(" ", strip=True)[:1500] if snippet else "",
        })
        if len(results) == 5:
            break
    return results
