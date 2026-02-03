"""Node API endpoints."""

from bson import ObjectId
from fastapi import APIRouter
from mm_base6 import cbv
from mm_mongo import MongoDeleteResult
from mm_result import Result
from starlette.responses import PlainTextResponse

from app.core.db import Node
from app.core.types import AppView

router = APIRouter(prefix="/api/nodes", tags=["node"])


@cbv(router)
class CBV(AppView):
    """Node-related API endpoints."""

    @router.get("/")
    async def get_nodes(self) -> list[Node]:
        """Get all nodes."""
        return await self.core.db.node.find({})

    @router.get("/export", response_class=PlainTextResponse)
    async def export_nodes(self) -> str:
        """Export all nodes as TOML."""
        return await self.core.services.node.export_as_toml()

    @router.get("/live")
    async def get_live_nodes(self) -> dict[str, list[str]]:
        """Get live node URLs grouped by network."""
        nodes = await self.core.services.node.get_live_nodes()
        return {network.value: [node.url for node in nodes] for network, nodes in nodes.items()}

    @router.post("/{id}/check")
    async def check_node(self, id: ObjectId) -> Result[int]:
        """Trigger a health check for a specific node."""
        return await self.core.services.node.check(id)

    @router.get("/{id}")
    async def get_node(self, id: ObjectId) -> Node:
        """Get a node by ID."""
        return await self.core.db.node.get(id)

    @router.delete("/{id}")
    async def delete_node(self, id: ObjectId) -> MongoDeleteResult:
        """Delete a node by ID."""
        return await self.core.db.node.delete(id)
