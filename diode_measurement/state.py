__all__ = ["State"]


class State:

    def __init__(self):
        self.state: dict = {}

    @property
    def measurement_type(self) -> str:
        return self.state.get("measurement_type", "")

    @property
    def timestamp(self) -> float:
        return self.state.get("timestamp", 0.0)

    @property
    def sample(self) -> str:
        return self.state.get("sample", "")

    @property
    def stop_requested(self) -> bool:
        return self.state.get("stop_requested", False)

    @property
    def auto_reconnect(self) -> bool:
        return self.state.get("auto_reconnect", False)

    @property
    def is_continuous(self) -> bool:
        return self.state.get("continuous", False)

    @property
    def is_reset(self) -> bool:
        return self.state.get("reset", False)

    @property
    def continue_in_compliance(self) -> bool:
        return self.state.get("continue_in_compliance", False)

    @property
    def waiting_time(self) -> float:
        return self.state.get("waiting_time", 1.0)

    @property
    def waiting_time_continuous(self) -> float:
        return self.state.get("waiting_time_continuous", 1.0)

    @property
    def source_voltage(self):
        return self.state.get("source_voltage")

    @property
    def bias_source_voltage(self):
        return self.state.get("bias_source_voltage")

    @property
    def bias_voltage(self) -> float:
        return self.state.get("bias_voltage", 0.0)

    @property
    def voltage_begin(self) -> float:
        return self.state.get("voltage_begin", 0.0)

    @property
    def voltage_end(self) -> float:
        return self.state.get("voltage_end", 0.0)

    @property
    def voltage_step(self) -> float:
        return self.state.get("voltage_step", 1.0)

    @property
    def current_compliance(self) -> float:
        return self.state.get("current_compliance", 0.0)

    @property
    def source_role(self):
        return self.state.get("source_role")

    @property
    def bias_source_role(self):
        return self.state.get("bias_source_role")

    @property
    def change_voltage_continuous(self):
        return self.state.get("change_voltage_continuous")

    def pop_change_voltage_continuous(self):
        return self.state.pop("change_voltage_continuous")

    def find_role(self, name: str) -> dict:
        return self.state.get("roles", {}).get(name, {})

    def update(self, kwargs):
        self.state.update(kwargs)

    def get(self, key, default=None):
        return self.state.get(key, default)

    def __iter__(self):
        return iter(self.state.items())
