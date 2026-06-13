from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from commerce_search.domain.catalog.entities import Product


class ProductRepository(Protocol):
    async def get(self, product_id: UUID) -> Product | None: ...

    async def save(self, product: Product) -> None: ...

    async def get_many(self, product_ids: Sequence[UUID]) -> Sequence[Product]: ...
