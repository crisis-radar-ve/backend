import re

import httpx


def _extract_text_from_html(html: str) -> str:
    """Very naive HTML to text extractor."""
    # Remove script and style tags
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    # Replace tags with spaces
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def fetch_url(url: str) -> dict:
    """Fetch a public URL and return title + text."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers={"User-Agent": "CrisisRadarBot/1.0"})
            response.raise_for_status()
        except httpx.HTTPError as e:
            return {"url": url, "title": None, "text": "", "error": str(e)}

    html = response.text
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else None
    text = _extract_text_from_html(html)

    return {"url": url, "title": title, "text": text, "error": None}
