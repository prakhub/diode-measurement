import logging
import math
import time
import threading

from typing import Any, Callable, Dict, List

from ..estimate import Estimate

from . import ReadingType, StateType, EventHandler, RangeMeasurement

__all__ = ["IVBiasMeasurement"]

logger = logging.getLogger(__name__)


class IVBiasMeasurement(RangeMeasurement):

    def __init__(self, state: StateType) -> None:
        super().__init__(state)
        self.iv_reading_event: EventHandler = EventHandler()

    def acquire_reading_data(self, voltage=None) -> ReadingType:
        smu = self.instruments.get("smu")
        smu2 = self.instruments.get("smu2")
        elm = self.instruments.get("elm")
        dmm = self.instruments.get("dmm")
        if voltage is None:
            voltage = self.get_source_voltage()
        i_smu = smu.read_current() if smu else math.nan
        i_smu2 = smu2.read_current() if smu2 else math.nan
        i_elm = elm.read_current() if elm else math.nan
        t_dmm = dmm.read_temperature() if dmm else math.nan
        return {
            "timestamp": time.time(),
            "voltage": voltage,
            "i_smu": i_smu,
            "i_smu2": i_smu2,
            "i_elm": i_elm,
            "t_dmm": t_dmm
        }

    def acquire_reading(self) -> None:
        reading: ReadingType = self.acquire_reading_data()
        logger.info(reading)
        # TODO
        if hasattr(self, "ivReadingLock") and hasattr(self, "ivReadingQueue"):
            with self.ivReadingLock:
                self.ivReadingQueue.append(reading)
        self.update_event({
            "smu_current": reading.get("i_smu"),
            "smu2_current": reading.get("i_smu2"),
            "elm_current": reading.get("i_elm"),
            "dmm_temperature": reading.get("t_dmm")
        })
        self.iv_reading_event(reading)

    def acquire_continuous_reading(self) -> None:
        t: float = time.time()
        interval: float = 1.0

        estimate: Estimate = Estimate(1)

        self.update_progress(0, 0, 0)

        def handle_reading(reading: ReadingType) -> None:
            """Handle a single reading, update UI and write to files."""
            logger.info(reading)
            self.it_reading_event(reading)

        voltage = self.get_source_voltage()

        while not self.stop_requested:
            dt: float = time.time() - t

            reading: ReadingType = self.acquire_reading_data(voltage=voltage)
            handle_reading(reading)

            # TODO
            if hasattr(self, "itReadingLock") and hasattr(self, "itReadingQueue"):
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

                self.update_event({
                    "smu_current": reading.get("i_smu"),
                    "smu2_current": reading.get("i_smu2"),
                    "elm_current": reading.get("i_elm"),
                    "dmm_temperature": reading.get("t_dmm")
                })

                t = time.time()

            if self.stop_requested:
                break

            self.apply_waiting_time_continuous(estimate)
            self.update_estimate_message_continuous("Reading...", estimate)

            estimate.advance()
