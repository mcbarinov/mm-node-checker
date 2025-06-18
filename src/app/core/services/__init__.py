from .node import NodeService
from .proxy import ProxyService


class ServiceRegistry:
    node: NodeService
    proxy: ProxyService
