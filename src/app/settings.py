from datetime import datetime

from fastapi import APIRouter
from mm_base6 import DC, DV, CoreConfig, DConfigModel, DValueModel, ServerConfig

core_config = CoreConfig()

server_config = ServerConfig()
server_config.tags = ["node"]
server_config.main_menu = {"/nodes": "nodes", "/networks": "networks", "/checks": "checks"}


class DConfigSettings(DConfigModel):
    proxies_url = DC("http://localhost:8000", "proxies url, each proxy on new line")
    limit_concurrent_checks = DC(10, "limit concurrent checks")


class DValueSettings(DValueModel):
    proxies: DV[list[str]] = DV([])
    proxies_updated_at: DV[datetime | None] = DV(None)


def get_router() -> APIRouter:
    from app.server.routers import check_router, node_router, ui_router

    router = APIRouter()
    router.include_router(ui_router.router)
    router.include_router(node_router.router)
    router.include_router(check_router.router)
    return router
