from decimal import Decimal
from uuid import uuid4

import pytest

from commerce_search.domain.catalog.entities import Product


def test_product_rejects_negative_price() -> None:
    with pytest.raises(ValueError, match="price"):
        Product(
            id=uuid4(),
            sku="SKU-001",
            name="Mechanical Keyboard",
            category_id=uuid4(),
            brand_id=None,
            price=Decimal("-0.01"),
        )
