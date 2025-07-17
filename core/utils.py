# /core/utils.py
# Universal utility functions for SoulOS — unique ID & timestamp generation.

import uuid
from datetime import datetime, timezone

def generate_uuid() -> str:
    """Generate a unique UUID4 string."""
    return str(uuid.uuid4())

def timestamp_now() -> str:
    """Return the current UTC ISO 8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()
