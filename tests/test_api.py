import asyncio

from httpx import ASGITransport, AsyncClient, Response

from apps.api.app.main import app


async def get_health() -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health")


def test_health() -> None:
    response = asyncio.run(get_health())

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Land to Homes API",
        "version": "0.1.0",
    }
