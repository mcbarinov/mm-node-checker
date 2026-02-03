"""Web UI page and action endpoints."""

from typing import Annotated

from fastapi import APIRouter, Form, Query
from mm_base6 import cbv, redirect
from mm_web3 import Network
from pydantic import BaseModel, BeforeValidator
from starlette.responses import HTMLResponse, RedirectResponse

from app.core.types import AppView


def empty_to_none(v: str | None) -> str | None:
    """Convert empty string to None for optional query params."""
    if v == "":
        return None
    return v


router = APIRouter(include_in_schema=False)


@cbv(router)
class PageCBV(AppView):
    """HTML page endpoints."""

    @router.get("/")
    async def index(self) -> HTMLResponse:
        """Render the index page."""
        return await self.render.html("index.j2")

    @router.get("/nodes")
    async def nodes(self, network: Annotated[Network | None, BeforeValidator(empty_to_none), Query()] = None) -> HTMLResponse:
        """Render the nodes list page, optionally filtered by network."""
        query = {}
        if network:
            query["network"] = network
        nodes = await self.core.db.node.find(query, "network")
        return await self.render.html("nodes.j2", form={"network": network}, nodes=nodes)

    @router.get("/networks")
    async def networks(self) -> HTMLResponse:
        """Render the networks overview page."""
        info = await self.core.services.node.get_networks_info()
        return await self.render.html("networks.j2", info=info)

    @router.get("/checks")
    async def checks(self) -> HTMLResponse:
        """Render the checks history page."""
        checks = await self.core.db.check.find({}, "created_at", limit=1000)
        return await self.render.html("checks.j2", checks=checks)


@cbv(router)
class ActionCBV(AppView):
    """Form action endpoints."""

    class AddNodes(BaseModel):
        """Form data for adding nodes."""

        network: Network
        urls: str

    @router.post("/nodes")
    async def add_nodes(self, form: Annotated[AddNodes, Form()]) -> RedirectResponse:
        """Handle add nodes form submission."""
        res = await self.core.services.node.add(form.network, form.urls)
        self.render.flash(f"nodes added: {res}")
        return redirect("/nodes")

    @router.post("/nodes/import")
    async def import_nodes(self, toml: Annotated[str, Form()]) -> RedirectResponse:
        """Handle import nodes from TOML form submission."""
        res = await self.core.services.node.import_from_toml(toml)
        self.render.flash(f"nodes imported: {res}")
        return redirect("/nodes")
