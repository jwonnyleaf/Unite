import aiohttp
from urllib.parse import urlparse


async def validImageURL(url: str) -> bool:
    """Check if the provided URL is a valid, accessible image."""
    try:
        res = urlparse(url)
        if not all([res.scheme, res.netloc]):
            return False

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return False

                content_type = response.headers.get("Content-Type", "")
                if not content_type.startswith("image/"):
                    return False

        return True
    except Exception:
        return False
