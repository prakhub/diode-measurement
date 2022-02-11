import contextlib
import logging
import math
import time

from PyQt5 import QtCore

from ..functions import LinearRange
from ..estimate import Estimate

from . import RangeMeasurement

__all__ = ['IVMeasurement']

logger = logging.getLogger(__name__)


class IVMeasurement(RangeMeasurement):

    ivReading = QtCore.pyqtSignal(dict)
    itReading = QtCore.pyqtSignal(dict)
    itChangeVoltageReady = QtCore.pyqtSignal()

    def __init__(self, state):
        super().__init__(state)
        self.ivReadingHandlers = []
        self.itReadingHandlers = []

    def acquireReadingData(self):
        smu = self.contexts.get('smu')
        elm = self.contexts.get('elm')
        dmm = self.contexts.get('dmm')
        voltage = self.get_source_voltage()
        if smu:
            i_smu = smu.read_current()
        else:
            i_smu = float('NaN')
        if elm:
            i_elm = elm.read_current()
        else:
            i_elm = float('NaN')
        if dmm:
            t_dmm = dmm.read_temperature()
        else:
            t_dmm = float('NaN')
        return {
            'timestamp': time.time(),
            'voltage': voltage,
            'i_smu': i_smu,
            'i_elm': i_elm,
            't_dmm': t_dmm
        }

    def acquireReading(self):
        reading = self.acquireReadingData()
        logger.info(reading)
        self.ivReading.emit(reading)
        self.update.emit({
            'smu_current': reading.get('i_smu'),
            'elm_current': reading.get('i_elm'),
            'dmm_temperature': reading.get('t_dmm')
        })
        for handler in self.ivReadingHandlers:
            handler(reading)

    def acquireContinuousReading(self):
        estimate = Estimate(1)
        while not self.stop_requested:
            #self.update_message("Reading...")
            self.update_progress(0, 0, 0)
            reading = self.acquireReadingData()
            logger.info(reading)
            self.itReading.emit(reading)
            self.update.emit({
                'smu_current': reading.get('i_smu'),
                'elm_current': reading.get('i_elm'),
                'dmm_temperature': reading.get('t_dmm')
            })
            for handler in self.itReadingHandlers:
                handler(reading)

            self.check_current_compliance()
            self.update_current_compliance()

            self.apply_change_voltage()

            self.apply_waiting_time_continuous(estimate)

            self.update_estimate_message_continuous("Reading...", estimate)
            estimate.advance()
