from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from commerce_search.shared.error_codes import ErrorCode


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    type: str | None = None


class ApiResponse[DataT](BaseModel):
    code: str
    message: str
    data: DataT | None = None
    request_id: str
    errors: list[ErrorDetail] | None = None


def success_response[DataT](
    data: DataT,
    *,
    request_id: str,
    message: str = "Success",
) -> ApiResponse[DataT]:
    return ApiResponse[DataT](
        code=ErrorCode.SUCCESS,
        message=message,
        data=data,
        request_id=request_id,
    )


def error_response(
    *,
    code: str,
    message: str,
    request_id: str,
    errors: Sequence[Mapping[str, Any]] | None = None,
) -> ApiResponse[None]:
    return ApiResponse[None](
        code=code,
        message=message,
        request_id=request_id,
        errors=[ErrorDetail.model_validate(error) for error in errors] if errors else None,
    )
