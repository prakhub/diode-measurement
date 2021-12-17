import contextlib
import logging
import math
import time

from PyQt5 import QtCore

from ..functions import LinearRange
from ..estimate import Estimate
from ..utils import inverse_square

from . import RangeMeasurement

__all__ = ['CVMeasurement']

logger = logging.getLogger(__name__)


class CVMeasurement(RangeMeasurement):

    cvReading = QtCore.pyqtSignal(dict)

    def __init__(self, state):
        super().__init__(state)
        self.cvReadingHandlers = []

    def extendCVReading(self, reading: dict) -> dict:
        # Calcualte 1c^2 as c2_lcr
        c_lcr = reading.get('c_lcr', math.nan)
        if math.isfinite(c_lcr) and c_lcr:
            reading['c2_lcr'] = inverse_square(c_lcr)
        else:
            reading['c2_lcr'] = math.nan
        return reading

    def acquireReadingData(self):
        smu = self.contexts.get('smu')
        lcr = self.contexts.get('lcr')
        dmm = self.contexts.get('dmm')
        voltage = self.get_source_voltage()
        if lcr:
            c_lcr = lcr.read_capacity()
        else:
            c_lcr = float('NaN')
        if smu:
            i_smu = smu.read_current()
        else:
            i_smu = float('NaN')
        if dmm:
            t_dmm = dmm.read_temperature()
        else:
            t_dmm = float('NaN')
        return {
            'timestamp': time.time(),
            'voltage': voltage,
            'i_smu': i_smu,
            'c_lcr': c_lcr,
            't_dmm': t_dmm
        }

    def acquireReading(self):
        reading = self.acquireReadingData()
        self.extendCVReading(reading)
        self.cvReading.emit(reading)
        self.update.emit({
            'smu_current': reading.get('i_smu'),
            'elm_current': reading.get('i_elm'),
            'lcr_capacity': reading.get('c_lcr'),
            'dmm_temperature': reading.get('t_dmm')
        })
        for handler in self.cvReadingHandlers:
            handler(reading)
