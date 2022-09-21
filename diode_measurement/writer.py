import csv
import math

from typing import Any, Dict, Optional

__all__ = ["Writer"]


def safe_format(value: Any, format_spec: str = None) -> str:
    """Safe format any value, return `NAN` if format fails."""
    try:
        return format(value, format_spec or "")
    except Exception:
        return format(math.nan)


def get_temperature(data: Dict[str, Any]) -> float:
    t_dmm = data.get("t_dmm")
    if isinstance(t_dmm, float):
        if math.isfinite(t_dmm):
            return t_dmm
    t_env = data.get("t_env")
    if isinstance(t_env, float):
        if math.isfinite(t_env):
            return t_env
    return math.nan


class Writer:

    delimiter = "\t"

    def __init__(self, fp) -> None:
        self._fp = fp
        self._writer = csv.writer(fp, delimiter=type(self).delimiter)
        self._current_table: Optional[str] = None

    def flush(self) -> None:
        self._fp.flush()

    def write_tag(self, key: str, value: Any) -> None:
        key = key.strip()
        value = format(value).strip()
        self._writer.writerow([f"{key}: {value}"])

    def write_table_header(self, columns: list) -> None:
        self._writer.writerow([])
        self._writer.writerow(columns)

    def write_table_row(self, columns: list) -> None:
        self._writer.writerow(columns)

    def write_meta(self, data: dict) -> None:
        self._current_table = None
        self.write_tag("sample", data.get("sample"))
        self.write_tag("measurement_type", data.get("measurement_type"))
        if "bias_voltage" in data:
            self.write_tag("bias_voltage[V]", safe_format(data.get("bias_voltage"), "+.3E"))
        self.write_tag("voltage_begin[V]", safe_format(data.get("voltage_begin"), "+.3E"))
        self.write_tag("voltage_end[V]", safe_format(data.get("voltage_end"), "+.3E"))
        self.write_tag("voltage_step[V]", safe_format(data.get("voltage_step"), "+.3E"))
        self.write_tag("waiting_time[s]", safe_format(data.get("waiting_time"), "+.3E"))
        self.write_tag("current_compliance[A]", safe_format(data.get("current_compliance"), "+.3E"))
        self.flush()

    def write_iv_row(self, data: dict) -> None:
        if self._current_table != "iv":
            self._current_table = "iv"
            self.write_table_header([
                "timestamp[s]",
                "voltage[V]",
                "i_smu[A]",
                "i_elm[A]",
                "temperature[degC]"
            ])
        self.write_table_row([
            safe_format(data.get("timestamp"), ".6f"),
            safe_format(data.get("voltage"), "+.3E"),
            safe_format(data.get("i_smu"), "+.3E"),
            safe_format(data.get("i_elm"), "+.3E"),
            safe_format(get_temperature(data), "+.3E")
        ])
        self.flush()

    def write_iv_bias_row(self, data: dict) -> None:
        if self._current_table != "iv":
            self._current_table = "iv"
            self.write_table_header([
                "timestamp[s]",
                "voltage[V]",
                "i_smu[A]",
                "i_smu2[A]",
                "i_elm[A]",
                "temperature[degC]"
            ])
        self.write_table_row([
            safe_format(data.get("timestamp"), ".6f"),
            safe_format(data.get("voltage"), "+.3E"),
            safe_format(data.get("i_smu"), "+.3E"),
            safe_format(data.get("i_smu2"), "+.3E"),
            safe_format(data.get("i_elm"), "+.3E"),
            safe_format(get_temperature(data), "+.3E")
        ])
        self.flush()

    def write_it_row(self, data: dict) -> None:
        if self._current_table != "it":
            self._current_table = "it"
            self.write_table_header([
                "timestamp[s]",
                "voltage[V]",
                "i_smu[A]",
                "i_elm[A]",
                "temperature[degC]"
            ])
        self.write_table_row([
            safe_format(data.get("timestamp"), ".6f"),
            safe_format(data.get("voltage"), "+.3E"),
            safe_format(data.get("i_smu"), "+.3E"),
            safe_format(data.get("i_elm"), "+.3E"),
            safe_format(get_temperature(data), "+.3E")
        ])
        self.flush()

    def write_it_bias_row(self, data: dict) -> None:
        if self._current_table != "it":
            self._current_table = "it"
            self.write_table_header([
                "timestamp[s]",
                "voltage[V]",
                "i_smu[A]",
                "i_smu2[A]",
                "i_elm[A]",
                "temperature[degC]"
            ])
        self.write_table_row([
            safe_format(data.get("timestamp"), ".6f"),
            safe_format(data.get("voltage"), "+.3E"),
            safe_format(data.get("i_smu"), "+.3E"),
            safe_format(data.get("i_smu2"), "+.3E"),
            safe_format(data.get("i_elm"), "+.3E"),
            safe_format(get_temperature(data), "+.3E")
        ])
        self.flush()

    def write_cv_row(self, data: dict) -> None:
        if self._current_table != "cv":
            self._current_table = "cv"
            self.write_table_header([
                "timestamp[s]",
                "voltage[V]",
                "i_smu[A]",
                "c_lcr[F]",
                "c2_lcr[1/F^2]",
                "temperature[degC]"
            ])
        self.write_table_row([
            safe_format(data.get("timestamp"), ".6f"),
            safe_format(data.get("voltage"), "+.3E"),
            safe_format(data.get("i_smu"), "+.3E"),
            safe_format(data.get("c_lcr"), "+.3E"),
            safe_format(data.get("c2_lcr"), "+.3E"),
            safe_format(get_temperature(data), "+.3E")
        ])
        self.flush()
