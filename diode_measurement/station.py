import logging
from typing import Any, Dict, Optional, Tuple, Type

from .driver import driver_factory
from .resource import Resource, AutoReconnectResource

logger = logging.getLogger(__name__)


class Station:

    def __init__(self) -> None:
        self.resources: Dict[str, Tuple[Type, Resource]] = {}
        self.contexts: Dict = {}

    def __enter__(self):
        logger.debug("creating instrument contexts...")
        self.contexts.clear()
        for key, value in self.resources.items():
            cls, resource = value
            logger.debug("creating instrument context %s: %s...", key, cls.__name__)
            context = cls(resource.__enter__())
            self.contexts[key] = context
        logger.debug("creating instrument contexts... done.")
        return self

    def __exit__(self, *exc):
        for _, resource in self.resources.values():
            resource.__exit__(*exc)
        self.contexts.clear()
        return False

    def register_instrument(self, name: str, role: Dict[str, Any], auto_reconnect: bool) -> None:
        if not role.get("enabled", False):
            return None
        model = role.get("model", "")
        resource_name = role.get("resource_name", "")
        if not resource_name.strip():
            raise ValueError(f"Empty resource name not allowed for {name.upper()} ({model}).")
        visa_library = role.get("visa_library", "")
        termination = role.get("termination", "\r\n")
        timeout = role.get("timeout", 4.0) * 1000  # in millisecs
        cls = driver_factory(model)
        if not cls:
            logger.warning("No such driver: %s", model)
            return None
        # If auto reconnect use experimental class AutoReconnectResource
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
