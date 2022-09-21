import re
from typing import Any, Dict, Optional

from .driver import Driver, InstrumentError, handle_exception

__all__ = ["EnvironBox"]


ERROR_MESSAGES: Dict[int, str] = {
    1: "RTC not running",
    2: "RTC read error",
    80: "DAC not found",
    90: "I/O Port Expander parameter error",
    99: "Invalid command",
    100: "General SET command error",
    199: "GET command parameter not found",
    200: "General GET command error",
    999: "Unknown command"
}


def parse_error(response: str) -> Optional[InstrumentError]:
    m = re.match(r"^err(\d+)", response.lower())
    if m:
        code = int(m.group(1))
        message = ERROR_MESSAGES.get(code, "Unknown error")
        return InstrumentError(code, message)
    return None


def parse_pc_data(response: str) -> Dict[str, Any]:
    values = response.split(",")
    relay_status = int(values[23])
    return {
        "box_humidity": float(values[1]),
        "box_temperature": float(values[2]),
        "power_microscope_ctrl": bool((relay_status >> 0) & 1),
        "power_box_light": bool((relay_status >> 1) & 1),
        "power_probecard_light": bool((relay_status >> 2) & 1),
        "power_laser_sensor": bool((relay_status >> 3) & 1),
        "power_probecard_camera": bool((relay_status >> 4) & 1),
        "power_microscope_camera": bool((relay_status >> 5) & 1),
        "power_microscope_light": bool((relay_status >> 6) & 1),
        "box_light": bool(int(values[24])),
        "box_door": bool(int(values[25])),
        "discharge_time": float(values[31]),
        "box_lux": float(values[32]),
        "pt100_1": float(values[33]),
        "pt100_2": float(values[34]),
    }


class EnvironBox(Driver):

    def __init__(self, resource):
        super().__init__(resource)
        self._error_queue = []
        self._temperature_source = "box_temperature"

    def identity(self) -> str:
        return self._query("*IDN?")

    def reset(self) -> None:
        self._error_queue.clear()
        self._temperature_source = "box_temperature"

    def clear(self) -> None:
        self._error_queue.clear()

    def next_error(self) -> Optional[InstrumentError]:
        if self._error_queue:
            return parse_error(self._error_queue.pop(0))
        return None

    def configure(self, options: Dict[str, Any]) -> None:
        temperature_source = options.get("temperature_source", "box_temperature")
        if temperature_source in ["box_temperature", "pt100_1", "pt100_2"]:
            self._temperature_source = temperature_source
        else:
            self._temperature_source = "box_temperature"

    def get_data(self) -> Dict[str, Any]:
        return parse_pc_data(self._query("GET:PC_DATA ?"))

    def read_temperature(self) -> float:
        return self.get_data().get(self._temperature_source, float("NaN"))  # TODO

    @handle_exception
    def _write(self, message):
        response = self.resource.query(message).strip()
        if response != "OK":
            self._error_queue.append(response)

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()
