"""Database models and collections."""

from __future__ import annotations

import enum
from datetime import datetime

from bson import ObjectId
from mm_base6 import BaseDb
from mm_mongo import AsyncMongoCollection, MongoModel
from mm_std import utc
from mm_web3 import Network
from pydantic import Field
from pymongo import IndexModel


@enum.unique
class NodeStatus(str, enum.Enum):
    """Status of a node after check."""

    NOT_CHECKED = "not_checked"
    OK = "ok"
    TIMEOUT = "timeout"
    PROXY = "proxy"
    UNKNOWN_RESPONSE = "unknown_response"
    ERROR = "error"

    @classmethod
    def from_error(cls, error: str) -> NodeStatus:
        """Convert error string to corresponding status."""
        if error == "timeout":
            return cls.TIMEOUT
        if error == "proxy":
            return cls.PROXY
        if error == "unknown_response":
            return cls.UNKNOWN_RESPONSE
        return cls.ERROR


class Node(MongoModel[ObjectId]):
    """Blockchain node with connection info and check history."""

    network: Network
    url: str
    status: NodeStatus = NodeStatus.NOT_CHECKED
    height: int | None = None  # latest block number or slot
    check_history: list[bool] = Field(default_factory=list)  # keep last 100 check results; ok=true, down=false
    checked_at: datetime | None = None  # last check
    last_ok_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc)

    @property
    def history_ok_count(self) -> int:
        """Count of successful checks in history."""
        return len([x for x in self.check_history if x is True])

    @property
    def history_down_count(self) -> int:
        """Count of failed checks in history."""
        return len([x for x in self.check_history if x is False])

    __collection__ = "node"
    __indexes__ = ["network", "!url", "last_ok_at"]


class Check(MongoModel[ObjectId]):
    """Single check result for a node."""

    network: Network
    url: str
    proxy: str | None
    status: NodeStatus
    elapsed: float  # response time in seconds
    response: dict[str, object]
    created_at: datetime = Field(default_factory=utc)

    __collection__ = "check"
    __indexes__ = ["network", IndexModel([("created_at", -1)], expireAfterSeconds=3 * 60 * 60)]


class Db(BaseDb):
    """Database collections."""

    node: AsyncMongoCollection[ObjectId, Node]
    check: AsyncMongoCollection[ObjectId, Check]
