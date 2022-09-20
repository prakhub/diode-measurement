import logging
from typing import Dict, Optional

from .driver import driver_factory
from .resource import Resource, AutoReconnectResource

logger = logging.getLogger(__name__)


class Station:

    def __init__(self, state: Dict) -> None:
        self.state: Dict = state
        self.resources: Dict = {}
        self.contexts: Dict = {}

    def register_instrument(self, name: str) -> None:
        role: Dict = self.state.get(name, {})
        if not role.get("enabled"):
            return None
        model = role.get("model")
        resource_name = role.get("resource_name")
        if not resource_name.strip():
            raise ValueError(f"Empty resource name not allowed for {name.upper()} ({model}).")
        visa_library = role.get("visa_library")
        termination = role.get("termination")
        timeout = role.get("timeout") * 1000  # in millisecs
        cls = driver_factory(model)
        if not cls:
            logger.warning("No such driver: %s", model)
            return None
        # If auto reconnect use experimental class AutoReconnectResource
        auto_reconnect = self.state.get("auto_reconnect", False)
        resource_cls = AutoReconnectResource if auto_reconnect else Resource
        resource = resource_cls(
            resource_name=resource_name,
            visa_library=visa_library,
            read_termination=termination,
            write_termination=termination,
            timeout=timeout
        )
        self.resources[name] = cls, resource
        return None

    def get(self, name: str) -> Optional[object]:
        return self.contexts.get(name)

    def reset(self) -> None:
        self.contexts.clear()
