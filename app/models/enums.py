from enum import Enum


class UserRole(str, Enum):
    """User role enum."""
    USER = "USER"
    ADMIN = "ADMIN"


class SentimentLabel(str, Enum):
    """Sentiment label enum."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
