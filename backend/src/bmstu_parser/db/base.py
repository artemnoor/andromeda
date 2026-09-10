"""Legacy facade for the canonical Andromeda database boundary."""

from andromeda.infrastructure.database.base import Base, create_engine_for_url

__all__ = ["Base", "create_engine_for_url"]
