import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from commerce_search.api.schemas import ApiResponse, success_response
from commerce_search.infrastructure.clients import InfrastructureClients
from commerce_search.infrastructure.dependencies import get_infrastructure_clients
from commerce_search.shared.exceptions import ServiceUnavailableError
from commerce_search.shared.middleware import get_request_id

router = APIRouter()


class HealthData(BaseModel):
    status: Literal["ok"]


class ReadinessData(HealthData):
    components: dict[str, Literal["ok"]]


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
    response_model=ApiResponse[ReadinessData],
    status_code=status.HTTP_200_OK,
    summary="检查服务是否可以接收流量",
)
async def readiness(
    request: Request,
    clients: Annotated[
        InfrastructureClients,
        Depends(get_infrastructure_clients),
    ],
) -> ApiResponse[ReadinessData]:
    probes = {
        "database": clients.database.ping(),
        "elasticsearch": clients.elasticsearch.ping(),
        "redis": clients.redis.ping(),
        "kafka": clients.kafka.ping(),
    }
    results = await asyncio.gather(*probes.values(), return_exceptions=True)
    failed_components = [
        {
            "field": component,
            "message": "Dependency health check failed",
            "type": type(result).__name__,
        }
        for component, result in zip(probes, results, strict=True)
        if isinstance(result, BaseException)
    ]
    if failed_components:
        raise ServiceUnavailableError(
            "One or more infrastructure dependencies are unavailable",
            code="INFRASTRUCTURE_UNAVAILABLE",
            errors=failed_components,
        )

    return success_response(
        ReadinessData(
            status="ok",
            components=dict.fromkeys(probes, "ok"),
        ),
        request_id=get_request_id(request),
    )
