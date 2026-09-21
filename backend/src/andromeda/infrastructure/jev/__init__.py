"""Optional external decision-model adapters.

The package intentionally contains no Jev SDK import. A provider-specific
transport can be injected by the composition root when it is explicitly
enabled; deterministic fallback remains the default.
"""

from .adapter import JevAdapterConfig, JevDecisionModelAdapter, JevTransport

__all__ = ["JevAdapterConfig", "JevDecisionModelAdapter", "JevTransport"]
