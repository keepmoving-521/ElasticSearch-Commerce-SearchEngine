from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from commerce_search.api.schemas import ApiResponse, success_response
from commerce_search.infrastructure.database.dependencies import get_database_manager
from commerce_search.infrastructure.database.manager import DatabaseManager
from commerce_search.shared.exceptions import ServiceUnavailableError
from commerce_search.shared.middleware import get_request_id

router = APIRouter()


class HealthData(BaseModel):
    status: Literal["ok"]


@router.get(
    "/live",
    response_model=ApiResponse[HealthData],
    status_code=status.HTTP_200_OK,
    summary="检查服务进程是否存活",
)
async def liveness(request: Request) -> ApiResponse[HealthData]:
    return success_response(
        HealthData(status="ok"),
        request_id=get_request_id(request),
    )


@router.get(
    "/ready",
    response_model=ApiResponse[HealthData],
    status_code=status.HTTP_200_OK,
    summary="检查服务是否可以接收流量",
)
async def readiness(
    request: Request,
    database: Annotated[DatabaseManager, Depends(get_database_manager)],
) -> ApiResponse[HealthData]:
    try:
        await database.ping()
    except Exception as exc:
        raise ServiceUnavailableError(
            "Database is unavailable",
            code="DATABASE_UNAVAILABLE",
        ) from exc

    return success_response(
        HealthData(status="ok"),
        request_id=get_request_id(request),
    )
