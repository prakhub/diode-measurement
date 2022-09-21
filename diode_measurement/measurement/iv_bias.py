import logging
import time
import threading

from typing import Any, Callable, Dict, List

from PyQt5 import QtCore

from ..estimate import Estimate

from . import RangeMeasurement

__all__ = ["IVBiasMeasurement"]

logger = logging.getLogger(__name__)


class IVBiasMeasurement(RangeMeasurement):

    itChangeVoltageReady = QtCore.pyqtSignal()

    def __init__(self, station, state: Dict[str, Any]) -> None:
        super().__init__(station, state)
        self.ivReadingHandlers: List[Callable] = []
        self.itReadingHandlers: List[Callable] = []

    def acquireReadingData(self, voltage=None):
        smu = self.station.get("smu")
        smu2 = self.station.get("smu2")
        elm = self.station.get("elm")
        dmm = self.station.get("dmm")
        env = self.station.get("env")
        if voltage is None:
            voltage = self.get_source_voltage()
        if smu:
            i_smu = smu.read_current()
        else:
            i_smu = float("NaN")
        if smu2:
            i_smu2 = smu2.read_current()
        else:
            i_smu2 = float("NaN")
        if elm:
            i_elm = elm.read_current()
        else:
            i_elm = float("NaN")
        if dmm:
            t_dmm = dmm.read_temperature()
        else:
            t_dmm = float("NaN")
        if env:
            t_env = env.read_temperature()
        else:
            t_env = float("NaN")
        return {
            "timestamp": time.time(),
            "voltage": voltage,
            "i_smu": i_smu,
            "i_smu2": i_smu2,
            "i_elm": i_elm,
            "t_dmm": t_dmm,
            "t_env": t_env,
        }

    def acquireReading(self):
        reading = self.acquireReadingData()
        logger.info(reading)
        with self.ivReadingLock:
            self.ivReadingQueue.append(reading)
        self.update.emit({
            "smu_current": reading.get("i_smu"),
            "smu2_current": reading.get("i_smu2"),
            "elm_current": reading.get("i_elm"),
            "dmm_temperature": reading.get("t_dmm"),
            "env_temperature": reading.get("t_env"),
        })
        for handler in self.ivReadingHandlers:
            handler(reading)

    def acquireContinuousReading(self):
        t = time.time()
        interval = 1.0

        estimate = Estimate(1)

        self.update_progress(0, 0, 0)

        def handle_reading(reading):
            """Handle a single reading, update UI and write to files."""
            logger.info(reading)
            for handler in self.itReadingHandlers:
                handler(reading)

        voltage = self.get_source_voltage()

        while not self.stop_requested:
            dt = time.time() - t

            reading = self.acquireReadingData(voltage=voltage)
            handle_reading(reading)

            with self.itReadingLock:
                self.itReadingQueue.append(reading)

            # Limit some actions for fast measurements
            if dt > interval:
                self.check_current_compliance()
                self.update_current_compliance()

                if self.bias_source_instrument:
                    self.check_bias_current_compliance()
                    self.update_bias_current_compliance()

                self.apply_change_voltage()

                voltage = self.get_source_voltage()

                self.update.emit({
                    "smu_current": reading.get("i_smu"),
                    "smu2_current": reading.get("i_smu2"),
                    "elm_current": reading.get("i_elm"),
                    "dmm_temperature": reading.get("t_dmm"),
                    "env_temperature": reading.get("t_env"),
                })

                t = time.time()

            if self.stop_requested:
                break

            self.apply_waiting_time_continuous(estimate)
            self.update_estimate_message_continuous("Reading...", estimate)

            estimate.advance()
