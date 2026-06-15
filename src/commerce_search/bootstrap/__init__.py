"""Application composition and lifecycle management."""

from commerce_search.bootstrap.container import ApplicationContainer
from commerce_search.bootstrap.lifecycle import create_lifespan

__all__ = ["ApplicationContainer", "create_lifespan"]
