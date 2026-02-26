"""Core constants for the application."""
from enum import Enum


class Platform(str, Enum):
    """Supported social media platforms."""
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    BLUESKY = "bluesky"
