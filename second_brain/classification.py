"""URL classification rules for the first Obsidian source folders."""


def classify_source(url: str, domain: str) -> str:
    """Classify a URL into Docs, Articles, Videos, or Repos."""
    lowered_url = url.lower()
    lowered_domain = domain.lower()

    if any(host in lowered_domain for host in ("youtube.com", "youtu.be", "vimeo.com")):
        return "Videos"
    if any(
        host in lowered_domain for host in ("github.com", "gitlab.com", "bitbucket.org")
    ):
        return "Repos"
    if any(
        token in lowered_url
        for token in ("/docs", "docs.", "documentation", "/learn", "developer.")
    ):
        return "Docs"
    return "Articles"
