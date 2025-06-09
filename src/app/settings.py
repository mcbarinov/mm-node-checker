from datetime import datetime

from fastapi import APIRouter
from mm_base6 import DC, DV, CoreConfig, DynamicConfigsModel, DynamicValuesModel, ServerConfig

# These configs will automatically load values from environment variables
# Make sure you have APP_NAME, DATA_DIR, DATABASE_URL, DOMAIN, ACCESS_TOKEN set
core_config = CoreConfig()  # pyright: ignore[reportCallIssue]

server_config = ServerConfig()  # pyright: ignore[reportCallIssue]
server_config.tags = ["node"]
server_config.main_menu = {"/nodes": "nodes", "/networks": "networks", "/checks": "checks"}


class DynamicConfigs(DynamicConfigsModel):
    proxies_url = DC("http://localhost:8000", "proxies url, each proxy on new line")
    limit_concurrent_checks = DC(10, "limit concurrent checks")
    auto_check = DC(True, "auto check nodes")


class DynamicValues(DynamicValuesModel):
    proxies: DV[list[str]] = DV([])
    proxies_updated_at: DV[datetime | None] = DV(None)


def get_router() -> APIRouter:
    from app.server import routers

    router = APIRouter()
    router.include_router(routers.ui.router)
    router.include_router(routers.node.router)
    router.include_router(routers.check.router)
    return router
