from decimal import Decimal

import pytest

from commerce_search.domain.search.models import SearchCriteria


def test_search_criteria_rejects_invalid_price_range() -> None:
    with pytest.raises(ValueError, match="minimum_price"):
        SearchCriteria(
            query="keyboard",
            minimum_price=Decimal("200"),
            maximum_price=Decimal("100"),
        )
