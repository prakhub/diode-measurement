import logging

import pyvisa

__all__ = ["ResourceError", "Resource"]

logger = logging.getLogger(__name__)


class ResourceError(Exception):

    pass


class Resource:

    def __init__(self, resource_name: str, visa_library: str, **options):
        self.resource_name = resource_name
        self.visa_library = visa_library
        self.options = {
            "read_termination": "\r\n",
            "write_termination": "\r\n",
            "timeout": 8000
        }
        self.options.update(options)
        self._resource = None

    def __enter__(self):
        try:
            rm = pyvisa.ResourceManager(self.visa_library)
            self._resource = rm.open_resource(resource_name=self.resource_name, **self.options)
        except pyvisa.Error as exc:
            raise ResourceError(f"{self.resource_name}: {exc}") from exc
        return self

    def __exit__(self, *exc):
        try:
            self._resource.close()
        finally:
            self._resource = None

    def query(self, message):
        try:
            self.write(message)
            return self.read()
        except pyvisa.Error as exc:
            raise ResourceError(f"{self.resource_name}: {exc}") from exc

    def write(self, message):
        try:
            logger.debug("resource.write: `%s`", message)
            return self._resource.write(message)
        except pyvisa.Error as exc:
            raise ResourceError(f"{self.resource_name}: {exc}") from exc

    def read(self):
        try:
            result = self._resource.read()
            logger.debug("resource.read: `%s`", result)
            return result
        except pyvisa.Error as exc:
            raise ResourceError(f"{self.resource_name}: {exc}") from exc

    def clear(self):
        self._resource.clear()
