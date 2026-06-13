from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SearchCriteria:
    query: str
    category_ids: tuple[UUID, ...] = ()
    brand_ids: tuple[UUID, ...] = ()
    minimum_price: Decimal | None = None
    maximum_price: Decimal | None = None
    page: int = 1
    page_size: int = 20
    filters: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("page must be greater than zero")
        if not 1 <= self.page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")
        if (
            self.minimum_price is not None
            and self.maximum_price is not None
            and self.minimum_price > self.maximum_price
        ):
            raise ValueError("minimum_price must not exceed maximum_price")
