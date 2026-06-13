from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Product:
    id: UUID
    sku: str
    name: str
    category_id: UUID
    brand_id: UUID | None
    price: Decimal
    attributes: dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValueError("sku must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if self.price < 0:
            raise ValueError("price must not be negative")
