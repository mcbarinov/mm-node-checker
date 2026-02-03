"""Node management service: CRUD operations and health checks."""

import logging
import time
from typing import cast

import anyio
import pydash
import tomlkit
from bson import ObjectId
from mm_base6 import Service
from mm_base6.core.utils import toml_dumps, toml_loads
from mm_concurrency import async_mutex
from mm_result import Result
from mm_std import utc
from mm_web3 import Network, NetworkType, random_proxy
from pydantic import BaseModel

from app.core import rpc
from app.core.db import Check, Node, NodeStatus
from app.core.types import AppCore

logger = logging.getLogger(__name__)


class NetworkInfo(BaseModel):
    """Summary info for a single network."""

    network: Network
    all_nodes: int
    live_nodes: int


class NodeService(Service[AppCore]):
    """Service for node management and health checks."""

    def configure_scheduler(self) -> None:
        """Schedule periodic node checks."""
        self.core.scheduler.add("check_next_node", 3, self.core.services.node.check_next)

    async def export_as_toml(self) -> str:
        """Export all nodes as TOML configuration."""
        nodes = []
        for network in Network:
            urls = await self.core.db.node.collection.distinct("url", {"network": network})
            if urls:
                nodes.append(
                    {
                        "network": network.value,
                        "urls": tomlkit.string("\n".join(urls), multiline=True),
                    }
                )

        return toml_dumps({"nodes": nodes})

    async def import_from_toml(self, toml: str) -> int:
        """Import nodes from TOML configuration, returns count of new nodes added."""
        result = 0
        data = cast(dict[str, list[dict[str, str]]], toml_loads(toml))  # tomlkit returns dict-like TOMLDocument
        for node in data["nodes"]:
            network = Network(node["network"])
            urls = node["urls"].strip().splitlines()
            urls = [url.strip().removesuffix("/") for url in urls if url.strip()]
            urls = pydash.uniq(urls)
            for url in urls:
                if await self.core.db.node.exists({"url": url}):
                    continue
                await self.core.db.node.insert_one(Node(id=ObjectId(), network=network, url=url))
                result += 1

        return result

    @async_mutex
    async def add(self, network: Network, urls_multiline: str) -> int:
        """Add nodes from multiline URL string, returns count of new nodes added."""
        result = 0
        urls = [url.strip().removesuffix("/") for url in urls_multiline.splitlines() if url.strip()]
        urls = pydash.uniq(urls)
        for url in urls:
            if await self.core.db.node.exists({"url": url}):
                continue
            await self.core.db.node.insert_one(Node(id=ObjectId(), network=network, url=url))
            result += 1

        return result

    async def check(self, id: ObjectId) -> Result[int]:
        """Check a single node's health and update its status."""
        node = await self.core.db.node.get(id)
        logger.info("check", extra={"url": node.url, "network": node.network.value})

        proxy = random_proxy(self.core.state.proxies)

        start_time = time.perf_counter()
        match node.network.network_type:
            case NetworkType.EVM:
                res = await rpc.get_evm_height(node.url, proxy=proxy)
            case NetworkType.SOLANA:
                res = await rpc.get_solana_height(node.url, proxy=proxy)
            case NetworkType.APTOS:
                res = await rpc.get_aptos_height(node.url, proxy=proxy)
            case NetworkType.STARKNET:
                res = await rpc.get_starknet_height(node.url, proxy=proxy)
            case _:
                raise NotImplementedError

        updated: dict[str, object] = {"checked_at": utc()}

        if res.is_ok():
            status = NodeStatus.OK
            updated["height"] = res.unwrap()
            updated["check_history"] = ([True, *node.check_history])[:100]
            updated["last_ok_at"] = utc()

        else:
            status = NodeStatus.from_error(res.unwrap_err())
            updated["height"] = None
            updated["check_history"] = ([False, *node.check_history])[:100]

        await self.core.db.check.insert_one(
            Check(
                id=ObjectId(),
                network=node.network,
                url=node.url,
                proxy=proxy,
                response=res.to_dict(safe_exception=True),
                status=status,
                elapsed=round(time.perf_counter() - start_time, 2),
            )
        )
        await self.core.db.node.set(id, updated | {"status": status})

        return res

    @async_mutex
    async def check_next(self) -> None:
        """Check the next batch of nodes that need checking."""
        if not self.core.settings.auto_check:
            return
        logger.debug("check_next")
        limit = self.core.settings.limit_concurrent_checks
        nodes = await self.core.db.node.find({"checked_at": None}, limit=limit)
        if len(nodes) < limit:
            nodes += await self.core.db.node.find(
                {"checked_at": {"$lt": utc(minutes=-1)}}, "checked_at", limit=limit - len(nodes)
            )

        async with anyio.create_task_group() as tg:
            for node in nodes:
                tg.start_soon(self.check, node.id, name=f"check_node_{node.id}")

    @async_mutex
    async def get_live_nodes(self) -> dict[Network, list[Node]]:
        """Get nodes that responded successfully in the last 5 minutes."""
        result: dict[Network, list[Node]] = {}
        for network in Network:
            result[network] = await self.core.db.node.find({"network": network, "last_ok_at": {"$gt": utc(minutes=-5)}})
        return result

    async def get_networks_info(self) -> list[NetworkInfo]:
        """Get summary info for all networks."""
        live_nodes = await self.get_live_nodes()
        return [
            NetworkInfo(
                network=network,
                live_nodes=len(live_nodes.get(network, [])),
                all_nodes=await self.core.db.node.count({"network": network}),
            )
            for network in Network
        ]
