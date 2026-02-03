"""Service layer for business logic."""

from .node import NodeService as NodeService
from .proxy import ProxyService as ProxyService


class ServiceRegistry:
    """Registry of all application services."""

    node: NodeService
    proxy: ProxyService
