import contextlib
import logging
import time

from typing import Any, Callable, Dict, List

from PyQt5 import QtCore

from ..functions import LinearRange
from ..estimate import Estimate

__all__ = ["Measurement", "RangeMeasurement"]

logger = logging.getLogger(__name__)


class Measurement(QtCore.QObject):

    started = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()
    update = QtCore.pyqtSignal(dict)
    failed = QtCore.pyqtSignal(object)

    def __init__(self, station, state: Dict[str, Any]) -> None:
        super().__init__()
        self.station = station
        self.state: Dict[str, Any] = state
        self.startedHandlers: List[Callable] = []
        self.finishedHandlers: List[Callable] = []

    def checkErrorState(self, context):
        error = context.next_error()
        if error:
            raise RuntimeError(f"Instrument Error: {error}")

    def update_rpc_state(self, state) -> None:
        self.update.emit({"rpc_state": state})

    @property
    def stop_requested(self) -> bool:
        return self.state.get("stop_requested") is True

    def initialize(self):
        pass

    def measure(self):
        pass

    def finalize(self):
        pass

    def run(self):
        try:
            logger.debug("run measurement...")
            self.update_rpc_state("configure")
            self.started.emit()
            logger.debug("handle started callbacks...")
            for handler in self.startedHandlers:
                handler()
            logger.debug("handle started callbacks... done.")
            self.station.reset()
            with contextlib.ExitStack() as stack:
                logger.debug("creating instrument contexts...")
                for key, value in self.station.resources.items():
                    cls, resource = value
                    logger.debug("creating instrument context %s: %s...", key, cls.__name__)
                    context = cls(stack.enter_context(resource))
                    self.station.contexts[key] = context
                logger.debug("creating instrument contexts... done.")
                try:
                    logger.debug("initialize...")
                    self.initialize()
                    logger.debug("initialize... done.")
                    logger.debug("measure...")
                    self.measure()
                    logger.debug("measure... done.")
                except Exception as exc:
                    logger.exception(exc)
                    self.failed.emit(exc)
                finally:
                    logger.debug("finalize...")
                    self.update_rpc_state("stopping")
                    self.finalize()
                    logger.debug("finalize... done.")
        except Exception as exc:
            logger.exception(exc)
            self.failed.emit(exc)
        finally:
            logger.debug("handle finished callbacks...")
            for handler in self.finishedHandlers:
                handler()
            logger.debug("handle finished callbacks... done.")
            self.station.reset()
            self.finished.emit()
            self.update_rpc_state("idle")
            logger.debug("run measurement... done.")


class RangeMeasurement(Measurement):

    @property
    def is_continuous(self) -> bool:
        return self.state.get("continuous") is True

    # Source

    def get_source_output_state(self):
        return self.source_instrument.get_output_enabled()

    def set_source_output_state(self, state):
        logger.info("Source output state: %s", state)
        self.source_instrument.set_output_enabled(state)
        self.update.emit({"source_output_state": state})
        self.state["source_output_state"] = state

    def get_source_voltage(self):
        return self.source_instrument.get_voltage_level()

    def set_source_voltage(self, voltage):
        logger.info("Source voltage level: %gV", voltage)
        self.source_instrument.set_voltage_level(voltage)
        self.update.emit({"source_voltage": voltage})
        self.state["source_voltage"] = voltage

    def set_source_voltage_range(self, voltage):
        logger.info("Source voltage range: %gV", voltage)
        self.source_instrument.set_voltage_range(voltage)

    # Bias source

    def get_bias_source_output_state(self):
        return self.bias_source_instrument.get_output_enabled()

    def set_bias_source_output_state(self, state):
        logger.info("Bias source output state: %s", state)
        self.bias_source_instrument.set_output_enabled(state)
        self.update.emit({"bias_source_output_state": state})
        self.state["bias_source_output_state"] = state

    def get_bias_source_voltage(self):
        return self.bias_source_instrument.get_voltage_level()

    def set_bias_source_voltage(self, voltage):
        logger.info("Bias source voltage level: %gV", voltage)
        self.bias_source_instrument.set_voltage_level(voltage)
        self.update.emit({"bias_source_voltage": voltage})
        self.state["bias_source_voltage"] = voltage

    def set_bias_source_voltage_range(self, voltage):
        logger.info("Bias source voltage range: %gV", voltage)
        self.bias_source_instrument.set_voltage_range(voltage)

    def check_current_compliance(self):
        """Raise exception if current compliance tripped and continue in
        compliance option is not active.
        """
        if not self.state.get("continue_in_compliance", False):
            if self.source_instrument.compliance_tripped():
                raise RuntimeError("Source compliance tripped!")

    def update_current_compliance(self):
        """Update current compliance if value changed."""
        current_compliance = self.state.get("current_compliance", 0.0)
        if self.current_compliance != current_compliance:
            self.current_compliance = current_compliance
            self.set_source_compliance(self.current_compliance)
            self.checkErrorState(self.source_instrument)

    def set_source_compliance(self, compiance):
        logger.info("Source current compliance level: %gA", compiance)
        self.source_instrument.set_current_compliance_level(compiance)

    def set_bias_source_compliance(self, compiance):
        logger.info("Bias source current compliance level: %gA", compiance)
        self.bias_source_instrument.set_current_compliance_level(compiance)

    def check_bias_current_compliance(self):
        """Raise exception if biascurrent compliance tripped and continue in
        compliance option is not active.
        """
        if not self.state.get("continue_in_compliance", False):
            if self.bias_source_instrument.compliance_tripped():
                raise RuntimeError("Source compliance tripped!")

    def update_bias_current_compliance(self):
        """Update current compliance if value changed."""
        current_compliance = self.state.get("current_compliance", 0.0)
        if self.bias_current_compliance != current_compliance:
            self.bias_current_compliance = current_compliance
            self.set_bias_source_compliance(self.bias_current_compliance)
            self.checkErrorState(self.bias_source_instrument)

    def apply_waiting_time(self):
        waiting_time = self.state.get("waiting_time", 1.0)
        logger.info("Waiting for %.2f sec", waiting_time)
        time.sleep(waiting_time)

    def apply_waiting_time_continuous(self, estimate):
        waiting_time = self.state.get("waiting_time_continuous", 1.0)
        logger.info("Waiting for %.2f sec", waiting_time)
        interval = 1.0
        if waiting_time < interval:
            time.sleep(waiting_time)
        else:
            now = time.time()
            threshold = now + waiting_time
            while now < threshold:
                if self.stop_requested:
                    self.update_message("Stopping...")
                    break
                if self.state.get("change_voltage_continuous"):
                    break
                remaining = round(threshold - now)
                self.update_estimate_message_continuous(f"Next reading in {remaining:d} sec...", estimate)
                time.sleep(interval)
                now = time.time()

    def apply_change_voltage(self):
        params = self.state.get("change_voltage_continuous")
        if params is not None:
            del self.state["change_voltage_continuous"]
            self.update_rpc_state("ramping")
            self.rampToContinuous(params.get("end_voltage"), params.get("step_voltage"), params.get("waiting_time"))
            if not self.stop_requested:  # hack
                self.update_rpc_state("continuous")
        self.itChangeVoltageReady.emit()

    def update_message(self, message: str) -> None:
        """Emit update message event."""
        self.update.emit({"message": message})

    def update_progress(self, begin: int, end: int, step: int) -> None:
        """Emit update progress event."""
        self.update.emit({"progress": (begin, end, step)})

    def update_estimate_message(self, message: str, estimate: Estimate) -> None:
        """Emit update message event for ramp iterations."""
        elapsed_time = format(estimate.elapsed).split(".")[0]
        remaining_time = format(estimate.remaining).split(".")[0]
        average_time = format(estimate.average.total_seconds(), ".2f")
        self.update_message(f"{message} | Elapsed {elapsed_time} | Remaining {remaining_time} | Average {average_time} s")

    def update_estimate_message_continuous(self, message: str, estimate: Estimate) -> None:
        """Emit update message event for continuous iterations."""
        elapsed_time = format(estimate.elapsed).split(".")[0]
        average_time = format(estimate.average.total_seconds(), ".3f")
        self.update_message(f"{message} | Elapsed {elapsed_time} | Average {average_time} s")

    def update_estimate_progress(self, estimate: Estimate) -> None:
        """Emit update progress event for ramp iterations."""
        self.update_progress(0, estimate.count, estimate.passed)

    def initialize(self):
        source = self.state.get("source")
        if source in self.station.contexts:
            self.source_instrument = self.station.get(source)
        else:
            raise RuntimeError("No source instrument set")

        # Bias

        self.bias_source_instrument = None
        if self.state.get("measurement_type") in ["iv_bias"]:
            bias_source = self.state.get("bias_source")
            if bias_source in self.station.contexts:
                self.bias_source_instrument = self.station.get(bias_source)
            else:
                raise RuntimeError("No bias source instrument set")

        logger.debug("querying context identities...")
        for key, context in self.station.contexts.items():
            logger.debug("reading %s identity...", key.upper())
            identity = context.identity()
            logger.debug("reading %s identity... done.", key.upper())
            logger.info("%s IDN: %s", key.upper(), identity)
        logger.debug("querying context identities... done.")

        logger.debug("get source output state...")
        source_output_state = self.get_source_output_state()
        logger.debug("get source output state... done.")

        if source_output_state:
            self.rampZero()
        else:
            self.set_source_voltage(0.0)

        # Bias

        if self.bias_source_instrument:
            logger.debug("get bias source output state...")
            bias_source_output_state = self.get_bias_source_output_state()
            logger.debug("get bias source output state... done.")

            if bias_source_output_state:
                self.rampBiasZero()
            else:
                self.set_bias_source_voltage(0.0)

        # Reset (optional)
        if self.state.get("reset"):
            for key, context in self.station.contexts.items():
                logger.info("Reset %s...", key.upper())
                context.reset()
                logger.info("Reset %s... done.", key.upper())

        # Clear state
        for key, context in self.station.contexts.items():
            logger.info("Clear %s...", key.upper())
            context.clear()
            logger.info("Clear %s... done.", key.upper())

        # Configure
        for key, context in self.station.contexts.items():
            logger.info("Configure %s...", key.upper())
            options: Dict[str, Any] = self.state.get(key, {}).get("options", {})
            for name, value in options.items():
                logger.info("%s: %r" , name, value)
            context.configure(options)
            self.checkErrorState(context)
            logger.info("Configure %s... done.", key.upper())

        # Compliance
        self.current_compliance = self.state.get("current_compliance", 0.0)
        self.set_source_compliance(self.current_compliance)
        self.checkErrorState(self.source_instrument)

        self.bias_current_compliance = self.state.get("current_compliance", 0.0)
        if self.bias_source_instrument:
            self.set_bias_source_compliance(self.bias_current_compliance)
            self.checkErrorState(self.bias_source_instrument)

        if self.bias_source_instrument:
            self.set_bias_source_output_state(True)
            self.rampBias()
            self.checkErrorState(self.bias_source_instrument)

        # Enable output
        self.set_source_output_state(True)

        elm = self.station.get("elm")
        if elm is not None:
            elm.set_zero_check_enabled(False)
            logger.info("ELM zero check: off")

        self.rampBegin()

        # Wait after output enable/ramp
        logger.debug("apply settle time...")
        time.sleep(1.0)
        logger.debug("apply settle time... done.")

    def measure(self):
        ramp = LinearRange(
            self.state.get("voltage_begin"),
            self.state.get("voltage_end"),
            self.state.get("voltage_step")
        )

        self.update_message(f"Ramp to {ramp.end} V")
        estimate = Estimate(len(ramp))

        self.update_rpc_state("ramping")

        for step, voltage in enumerate(ramp):
            self.update_estimate_message(f"Ramp to {ramp.end} V", estimate)
            self.update_estimate_progress(estimate)

            if self.stop_requested:
                self.update_message("Stopping...")
                return
            self.set_source_voltage(voltage)

            self.apply_waiting_time()

            self.acquireReading()

            self.check_current_compliance()
            self.update_current_compliance()

            if self.bias_source_instrument:
                self.check_bias_current_compliance()
                self.update_bias_current_compliance()

            estimate.advance()

        self.update_rpc_state("measure")

        self.update_message("")

        if self.stop_requested:
            self.update_message("Stopping...")
            return

        if self.is_continuous:
            self.update_message("Continuous measurement...")
            self.update_rpc_state("continuous")
            self.acquireContinuousReading()

    def finalize(self):
        try:
            elm = self.station.get("elm")
            if elm is not None:
                elm.set_zero_check_enabled(True)
                logger.info("ELM zero check: on")

            self.rampZero()

            if self.bias_source_instrument:
                self.rampBiasZero()

            # HACK: wait until capacitors discared before output disable
            def read_source_voltage():
                if hasattr(self.source_instrument, "read_voltage"):
                    return self.source_instrument.read_voltage()
                logger.warning("Source instrument does not provide voltage readings.")
                return 0.

            threshold = 0.5  # Volt

            self.update_message("Waiting for voltage settled...")
            self.update_progress(0, 0, 0)

            t = time.time()

            while abs(read_source_voltage()) > threshold:
                time.sleep(1.0)

                dt = time.time() - t
                if dt > 60.0:
                    raise RuntimeError(f"Timeout while waiting for voltage to settle < {threshold} V, source output still enabled.")

            self.update_message("")

            # HACK: end

            self.set_source_output_state(False)

            if self.bias_source_instrument:
                self.set_bias_source_output_state(False)

        finally:
            self.update.emit({
                "source_voltage": None,
                "bias_source_voltage": None,
                "smu_current": None,
                "smu2_current": None,
                "elm_current": None,
                "lcr_capacity": None,
                "dmm_temperature": None
            })

    def acquireReading(self):
        pass

    def acquireContinuousReading(self):
        pass

    def rampBegin(self):
        # Set voltage range to end voltage
        voltage_end = self.state.get("voltage_end")
        self.set_source_voltage_range(voltage_end)

        voltage_begin = self.state.get("voltage_begin", 0.0)
        ramp = LinearRange(
            self.state.get("source_voltage", 0.0),
            voltage_begin,
            5.0
        )
        estimate = Estimate(len(ramp))

        for step, voltage in enumerate(ramp):
            self.update_estimate_message(f"Ramp to {ramp.end} V", estimate)
            self.update_estimate_progress(estimate)

            if self.stop_requested:
                break
            self.set_source_voltage(voltage)
            time.sleep(.250)
            estimate.advance()

    def rampZero(self):
        source_voltage = self.state.get("source_voltage", 0.0)
        self.update.emit({
            "smu_current": None,
            "smu2_current": None,
            "elm_current": None,
            "lcr_capacity": None,
            "dmm_temperature": None
        })
        ramp = LinearRange(source_voltage, 0.0, 5.0)
        estimate = Estimate(len(ramp))
        logging.info("Ramp source to zero...")
        for step, voltage in enumerate(ramp):
            self.update_estimate_message(f"Ramp to {ramp.end} V", estimate)
            self.update_estimate_progress(estimate)

            self.set_source_voltage(voltage)
            time.sleep(.250)
            estimate.advance()
        logging.info("Ramp source to zero... done.")

    def rampBias(self):
        bias_voltage = self.state.get("bias_voltage", 0.0)
        self.set_bias_source_voltage_range(bias_voltage)

        voltage_begin = 0.0
        ramp = LinearRange(
            voltage_begin,
            bias_voltage,
            5.0
        )
        estimate = Estimate(len(ramp))

        logging.info("Ramp bias source to %g V...", ramp.end)
        for step, voltage in enumerate(ramp):
            self.update_estimate_message(f"Ramp bias to {ramp.end} V", estimate)
            self.update_estimate_progress(estimate)

            if self.stop_requested:
                break
            self.set_bias_source_voltage(voltage)
            time.sleep(.250)
            estimate.advance()
        logging.info("Ramp bias source to %g V... done.", ramp.end)

    def rampBiasZero(self):
        bias_source_voltage = self.state.get("bias_source_voltage", 0.0)
        self.update.emit({
            "smu_current": None,
            "smu2_current": None,
            "elm_current": None,
            "lcr_capacity": None,
            "dmm_temperature": None
        })
        ramp = LinearRange(bias_source_voltage, 0.0, 5.0)
        estimate = Estimate(len(ramp))
        logging.info("Ramp bias source to zero...")
        for step, voltage in enumerate(ramp):
            self.update_estimate_message(f"Ramp bias to {ramp.end} V", estimate)
            self.update_estimate_progress(estimate)

            self.set_bias_source_voltage(voltage)
            time.sleep(.250)
            estimate.advance()
        logging.info("Ramp bias source to zero... done.")

    def rampToContinuous(self, end_voltage, step_voltage, waiting_time):
        source_voltage = self.state.get("source_voltage", 0.0)

        ramp = LinearRange(source_voltage, end_voltage, step_voltage)
        estimate = Estimate(len(ramp))

        # If end voltage higher, set new range before ramp.
        if abs(ramp.end) > abs(ramp.begin):
            self.set_source_voltage_range(ramp.end)

        for step, voltage in enumerate(ramp):
            self.update_estimate_message(f"Ramp to {ramp.end} V", estimate)
            self.update_estimate_progress(estimate)

            if self.stop_requested:
                self.update_message("Stopping...")
                return

            self.set_source_voltage(voltage)

            time.sleep(waiting_time)

            reading = self.acquireReadingData()
            logger.info(reading)

            with self.itReadingLock:
                self.itReadingQueue.append(reading)

            for handler in self.itReadingHandlers:
                handler(reading)

            self.update.emit({
                "smu_current": reading.get("i_smu"),
                "smu2_current": reading.get("i_smu2"),
                "elm_current": reading.get("i_elm")
            })

            self.check_current_compliance()
            self.update_current_compliance()

            if self.bias_source_instrument:
                self.check_bias_current_compliance()
                self.update_bias_current_compliance()

            estimate.advance()

        # If end voltage lower, set new range after ramp.
        if abs(ramp.end) < abs(ramp.begin):
            self.set_source_voltage_range(ramp.end)
