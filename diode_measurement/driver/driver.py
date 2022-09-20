import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

__all__ = ["Driver"]


def handle_exception(method):
    def handle_exception(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            raise DriverError(f"{type(self).__name__}: {exc}") from exc
    return handle_exception


class InstrumentError:

    def __init__(self, code: int, message: str) -> None:
        self.code: int = code
        self.message: str = message

    def __eq__(self, other) -> bool:
        if isinstance(other, InstrumentError):
            return self.code, self.message == other.code, other.message
        elif isinstance(other, tuple) and len(other) == 2:
            return self.code, self.message == other[0], other[1]
        return super().__eq__(other)

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


def parse_scpi_error(response: str) -> Optional[InstrumentError]:
    code, message = response.split(",", 1)
    code = int(code)
    message = message.strip().strip('"')
    if code:
        return InstrumentError(code, message)
    return None


def parse_tsp_error(response: str) -> Optional[InstrumentError]:
    code, message, *_ = response.split("\t")
    code = int(float(code))
    message = message.strip().strip('"')
    if code:
        return InstrumentError(code, message)
    return None


class DriverError(Exception):

    ...


class Driver(ABC):

    def __init__(self, resource):
        self.resource = resource

    @abstractmethod
    def identity(self) -> str:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def next_error(self) -> Optional[InstrumentError]:
        ...

    @abstractmethod
    def configure(self, options: Dict[str, Any]) -> None:
        ...


class SourceMeter(Driver):

    @abstractmethod
    def get_output_enabled(self) -> bool:
        ...

    @abstractmethod
    def set_output_enabled(self, enabled: bool) -> None:
        ...

    @abstractmethod
    def get_voltage_level(self) -> float:
        ...

    @abstractmethod
    def set_voltage_level(self, level: float) -> None:
        ...

    @abstractmethod
    def set_voltage_range(self, level: float) -> None:
        ...

    @abstractmethod
    def set_current_compliance_level(self, level: float) -> None:
        ...

    @abstractmethod
    def compliance_tripped(self) -> bool:
        ...

    @abstractmethod
    def read_current(self) -> float:
        ...


class Electrometer(SourceMeter):

    @abstractmethod
    def set_zero_check_enabled(self, enabled: bool) -> None:
        ...


class LCRMeter(SourceMeter):

    @abstractmethod
    def read_capacity(self) -> float:
        ...


class DMM(Driver):

    @abstractmethod
    def read_temperature(self) -> float:
        ...
