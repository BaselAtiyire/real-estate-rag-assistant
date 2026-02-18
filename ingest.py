import requests
import trafilatura

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def fetch_url_text(url: str) -> str:
    """
    Extract main article text from a URL.
    Uses trafilatura (best effort) with requests fallback.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        html = downloaded

        if not html:
            resp = requests.get(url, timeout=25, headers={"User-Agent": UA})
            resp.raise_for_status()
            html = resp.text

        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )
        return (text or "").strip()
    except Exception:
        return ""
