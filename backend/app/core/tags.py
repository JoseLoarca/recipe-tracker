"""Tag name normalization.

Tags are freeform (typed by users or suggested by the LLM extraction), but
normalized on write so near-duplicates like "Air Fryer" and "air fryer "
don't proliferate — without needing a dedicated tag-admin UI.
"""


def normalize_tag_name(name: str) -> str:
    """Normalize a tag name for storage and deduplication.

    Args:
        name: The raw tag text, as typed or extracted.

    Returns:
        The trimmed, lowercased tag name.

    Raises:
        ValueError: If the normalized name is empty.
    """
    normalized = name.strip().lower()
    if not normalized:
        raise ValueError("Tag name cannot be empty")
    return normalized
