from typing import Any


def matches(query: str, obj: Any) -> bool:
    """
    Returns whether the given query matches the given object.
    """
    return normalized(query) in normalized(str(obj))


def normalized(text: str) -> str:
    """
    Returns the given text normalized for comparison.
    """
    return ''.join(c.lower() for c in text if c.isalnum())
