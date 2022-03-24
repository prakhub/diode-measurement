import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

__all__ = ['Driver']


def handle_exception(method):
    def handle_exception(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            raise DriverError(f"{type(self).__name__}: {exc}") from exc
    return handle_exception


class DriverError(Exception):

    pass


class Driver(ABC):

    def __init__(self, resource):
        self.resource = resource

    @abstractmethod
    def identity(self) -> str:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def error_state(self) -> tuple:
        pass

    @abstractmethod
    def configure(self, **options) -> None:
        pass


class SourceMeter(Driver):

    @abstractmethod
    def get_output_enabled(self) -> bool:
        pass

    @abstractmethod
    def set_output_enabled(self, enabled: bool) -> None:
        pass

    @abstractmethod
    def get_voltage_level(self) -> float:
        pass

    @abstractmethod
    def set_voltage_level(self, level: float) -> None:
        pass

    @abstractmethod
    def set_voltage_range(self, level: float) -> None:
        pass

    @abstractmethod
    def set_current_compliance_level(self, level: float) -> None:
        pass

    @abstractmethod
    def compliance_tripped(self) -> bool:
        pass

    @abstractmethod
    def read_current(self) -> float:
        pass


class Electrometer(SourceMeter):

    pass


class LCRMeter(SourceMeter):

    @abstractmethod
    def read_capacity(self) -> float:
        pass


class DMM(Driver):

    @abstractmethod
    def read_temperature(self) -> float:
        pass
