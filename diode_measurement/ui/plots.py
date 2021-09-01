import os

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtChart

from ..utils import auto_scale

__all__ = [
    "IVPlotWidget",
    "ItPlotWidget",
    "CVPlotWidget",
    "CV2PlotWidget"
]

class DynamicValueAxis(QtChart.QValueAxis):

    def __init__(self, axis, unit):
        super().__init__(axis)
        self.setProperty('axis', axis)
        self.setUnit(unit)
        self.setLocked(False)
        self.setRange(axis.min(), axis.max())
        axis.rangeChanged.connect(self.setRange)
        axis.hide()

    def axis(self):
        return self.property('axis')

    def unit(self):
        return self.property('unit')

    def setUnit(self, unit):
        return self.setProperty('unit', unit)

    def setLocked(self, state):
        self.setProperty('locked', state)

    def setRange(self, minimum, maximum):
        if not self.property('locked'):
            unit = self.unit()
            scale, prefix, _ = auto_scale(max(minimum, maximum))
            self.setLabelFormat(f'%G {prefix}{unit}')
            minimum *= 1 / scale
            maximum *= 1 / scale
            super().setRange(minimum, maximum)

class LimitsAggregator(QtCore.QObject):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._minimum: float = 0.
        self._maximum: float = 0.
        self._valid: bool = False

    def isValid(self) -> bool:
        return self._valid

    def clear(self) -> None:
        self._minimum = 0.
        self._maximum = 0.
        self._valid = False

    def append(self, value: float) -> None:
        if self._valid:
            self._minimum = min(self.minimum(), value)
            self._maximum = max(self.maximum(), value)
        else:
            self._minimum = value
            self._maximum = value
        self._valid = True

    def minimum(self) -> float:
        return self._minimum

    def maximum(self) -> float:
        return self._maximum

class PlotToolButton(QtWidgets.QPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, 18)

class PlotWidget(QtChart.QChartView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart = QtChart.QChart()
        self.chart.setMargins(QtCore.QMargins(4, 4, 4, 4))
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setBackgroundRoundness(0)
        self.chart.legend().setAlignment(QtCore.Qt.AlignRight)
        self.setChart(self.chart)

        self.setRubberBand(QtChart.QChartView.RectangleRubberBand)

        self.toolbar = QtWidgets.QWidget()
        self.toolbar.setObjectName("toolbar")
        self.toolbar.setStyleSheet("QWidget#toolbar{ background: transparent; }")
        proxy = self.scene().addWidget(self.toolbar)
        proxy.setPos(2, 2)
        proxy.setZValue(10000)
        # Set parent after adding widget to scene to trigger
        # widgets destruction on close of chart view.
        self.toolbar.setParent(self)
        self.toolbar.hide()

        self.resetButton = PlotToolButton()
        self.resetButton.setText("R")
        self.resetButton.setToolTip("Reset plot")
        self.resetButton.setStatusTip("Reset plot")
        self.resetButton.clicked.connect(self.reset)

        self.saveAsButton = PlotToolButton()
        self.saveAsButton.setText("S")
        self.saveAsButton.setToolTip("Save plot as PNG")
        self.saveAsButton.setStatusTip("Save plot as PNG")
        self.saveAsButton.clicked.connect(self.saveAs)

        layout = QtWidgets.QVBoxLayout(self.toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.resetButton)
        layout.addWidget(self.saveAsButton)

        self.series = {}

    def mouseMoveEvent(self, event):
        self.toolbar.setVisible(self.underMouse())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.toolbar.hide()
        super().leaveEvent(event)

    @QtCore.pyqtSlot()
    def reset(self):
        self.chart.zoomReset()

    @QtCore.pyqtSlot()
    def saveAs(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save File",
            ".",
            "PNG Image (*.png);;"
        )
        if filename:
            if os.path.splitext(filename)[1] != ".png":
                filename = f"{filename}.png"
            try:
                self.grab().save(filename)
            except Exception as exc:
                pass

    def clear(self):
        for series in self.chart.series():
            series.clear()

    def isReverse(self):
        for series in self.chart.series():
            if series.count():
                if series.at(series.count() - 1).x() < series.at(0).x():
                    return True
        return False

class IVPlotWidget(PlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart.setTitle("I vs. V")

        self.smuSeries = QtChart.QLineSeries()
        self.smuSeries.setName("SMU")
        self.smuSeries.setColor(QtCore.Qt.red)
        self.smuSeries.setPointsVisible(True)
        self.chart.addSeries(self.smuSeries)

        self.elmSeries = QtChart.QLineSeries()
        self.elmSeries.setName("ELM")
        self.elmSeries.setColor(QtCore.Qt.blue)
        self.elmSeries.setPointsVisible(True)
        self.chart.addSeries(self.elmSeries)

        self.iAxis = QtChart.QValueAxis()
        self.chart.addAxis(self.iAxis, QtCore.Qt.AlignLeft)
        self.smuSeries.attachAxis(self.iAxis)
        self.elmSeries.attachAxis(self.iAxis)

        self.iDynamicAxis = DynamicValueAxis(self.iAxis, 'A')
        self.iDynamicAxis.setTitleText("Current")
        self.iDynamicAxis.setTickCount(9)
        self.chart.addAxis(self.iDynamicAxis, QtCore.Qt.AlignLeft)
        self.iAxis.setRange(0, 200e-9)

        self.vAxis = QtChart.QValueAxis()
        self.vAxis.setTitleText("Voltage")
        self.vAxis.setLabelFormat("%g V")
        self.vAxis.setRange(-100, +100)
        self.chart.addAxis(self.vAxis, QtCore.Qt.AlignBottom)
        self.smuSeries.attachAxis(self.vAxis)
        self.elmSeries.attachAxis(self.vAxis)

        self.iLimits = LimitsAggregator(self)
        self.vLimits = LimitsAggregator(self)

        self.series['smu'] = self.smuSeries
        self.series['elm'] = self.elmSeries

    def fitVAxis(self) -> None:
        self.vAxis.setReverse(self.isReverse())
        if self.vLimits.isValid():
            minimum = self.vLimits.minimum()
            maximum = self.vLimits.maximum()
        else:
            minimum = 0
            maximum = 100
        self.vAxis.setRange(minimum, maximum)

    def fitIAxis(self) -> None:
        if self.iLimits.isValid():
            minimum = self.iLimits.minimum()
            maximum = self.iLimits.maximum()
        else:
            minimum = 0
            maximum = 200e-9
        if minimum == maximum:
            maximum += 0.1
        self.iDynamicAxis.setLocked(True)
        self.iAxis.setRange(minimum, maximum)
        self.iDynamicAxis.setLocked(False)
        self.iAxis.applyNiceNumbers()

    def fit(self) -> None:
        if self.chart.isZoomed():
            return
        self.fitVAxis()
        self.fitIAxis()

    def clear(self) -> None:
        super().clear()
        self.iLimits.clear()
        self.vLimits.clear()

    def append(self, name: str, x: float, y: float) -> None:
        series = self.series.get(name)
        if series is not None:
            series.append(x, y)
            self.iLimits.append(y)
            self.vLimits.append(x)
            self.fit()

class ItPlotWidget(PlotWidget):

    MAX_POINTS = 60 * 60 * 24

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart.setTitle("I vs. t")

        self.smuSeries = QtChart.QLineSeries()
        self.smuSeries.setName("SMU")
        self.smuSeries.setColor(QtCore.Qt.red)
        self.smuSeries.setPointsVisible(True)
        self.chart.addSeries(self.smuSeries)

        self.elmSeries = QtChart.QLineSeries()
        self.elmSeries.setName("ELM")
        self.elmSeries.setColor(QtCore.Qt.blue)
        self.elmSeries.setPointsVisible(True)
        self.chart.addSeries(self.elmSeries)

        self.iAxis = QtChart.QValueAxis()
        self.iAxis.hide()
        self.chart.addAxis(self.iAxis, QtCore.Qt.AlignLeft)
        self.smuSeries.attachAxis(self.iAxis)
        self.elmSeries.attachAxis(self.iAxis)

        self.iDynamicAxis = DynamicValueAxis(self.iAxis, 'A')
        self.iDynamicAxis.setTitleText("Current")
        self.iDynamicAxis.setTickCount(9)
        self.chart.addAxis(self.iDynamicAxis, QtCore.Qt.AlignLeft)
        self.iAxis.setRange(0, 200e-9)

        self.tAxis = QtChart.QDateTimeAxis()
        self.tAxis.setTitleText("Time")
        self.tAxis.setTickCount(3)
        self.chart.addAxis(self.tAxis, QtCore.Qt.AlignBottom)
        self.smuSeries.attachAxis(self.tAxis)
        self.elmSeries.attachAxis(self.tAxis)

        self.iLimits = LimitsAggregator(self)
        self.tLimits = LimitsAggregator(self)

        self.series['smu'] = self.smuSeries
        self.series['elm'] = self.elmSeries

    def fitTAxis(self) -> None:
        if self.tLimits.isValid():
            minimum = self.tLimits.minimum()
            maximum = self.tLimits.maximum()
        else:
            import time
            t = time.time()
            minimum = t-60
            maximum = t
        t0 = QtCore.QDateTime.fromMSecsSinceEpoch(minimum * 1e3)
        t1 = QtCore.QDateTime.fromMSecsSinceEpoch(maximum * 1e3)
        self.tAxis.setRange(t0, t1)

    def fitIAxis(self) -> None:
        if self.iLimits.isValid():
            minimum = self.iLimits.minimum()
            maximum = self.iLimits.maximum()
        else:
            minimum = 0
            maximum = 200e-9
        if minimum == maximum:
            maximum += 0.1
        self.iDynamicAxis.setLocked(True)
        self.iAxis.setRange(minimum, maximum)
        self.iDynamicAxis.setLocked(False)
        self.iAxis.applyNiceNumbers()

    def fit(self):
        if self.chart.isZoomed():
            return
        self.fitTAxis()
        self.fitIAxis()

    def clear(self) -> None:
        super().clear()
        self.iLimits.clear()
        self.tLimits.clear()

    def append(self, name: str, x: float, y: float) -> None:
        series = self.series.get(name)
        if series is not None:
            series.append(QtCore.QPointF(x * 1e3, y))
            if series.count() > self.MAX_POINTS:
                series.remove(0)
            self.iLimits.append(y)
            self.tLimits.append(x)
            self.fit()

class CVPlotWidget(PlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart.setTitle("C vs. V")

        self.lcrSeries = QtChart.QLineSeries()
        self.lcrSeries.setName("LCR")
        self.lcrSeries.setColor(QtCore.Qt.magenta)
        self.chart.addSeries(self.lcrSeries)

        self.cAxis = QtChart.QValueAxis()
        self.chart.addAxis(self.cAxis, QtCore.Qt.AlignLeft)
        self.lcrSeries.attachAxis(self.cAxis)

        self.cDynamicAxis = DynamicValueAxis(self.cAxis, 'F')
        self.cDynamicAxis.setTitleText("Capacitance")
        self.cDynamicAxis.setTickCount(9)
        self.chart.addAxis(self.cDynamicAxis, QtCore.Qt.AlignLeft)
        self.cAxis.setRange(0, 200e-9)

        self.vAxis = QtChart.QValueAxis()
        self.vAxis.setTitleText("Voltage")
        self.vAxis.setLabelFormat("%g V")
        self.vAxis.setRange(0, 200)
        self.vAxis.setTickCount(9)
        self.chart.addAxis(self.vAxis, QtCore.Qt.AlignBottom)
        self.lcrSeries.attachAxis(self.vAxis)

        self.cLimits = LimitsAggregator(self)
        self.vLimits = LimitsAggregator(self)

        self.series['lcr'] = self.lcrSeries

    def fit(self):
        if self.chart.isZoomed():
            return
        minimum = self.vLimits.minimum()
        maximum = self.vLimits.maximum()
        self.vAxis.setReverse(minimum > maximum)
        minimum, maximum = sorted((minimum, maximum))
        self.vAxis.setRange(minimum, maximum)
        self.cDynamicAxis.setLocked(True)
        self.cAxis.setRange(self.cLimits.minimum(), self.cLimits.maximum())
        self.cDynamicAxis.setLocked(False)
        self.cAxis.applyNiceNumbers()

    def clear(self) -> None:
        super().clear()
        self.cLimits.clear()
        self.vLimits.clear()

    def append(self, name, x, y):
        series = self.series.get(name)
        if series is not None:
            series.append(x, y)
            self.cLimits.append(y)
            self.vLimits.append(x)
            self.fit()

class CV2PlotWidget(PlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart.setTitle("1/C^2 vs. V")

        self.lcrSeries = QtChart.QLineSeries()
        self.lcrSeries.setName("LCR")
        self.lcrSeries.setColor(QtCore.Qt.magenta)
        self.chart.addSeries(self.lcrSeries)

        self.cAxis = QtChart.QValueAxis()
        self.cAxis.setTitleText("Capacitance [1/pF^2]")
        self.cAxis.setLabelFormat("%g")
        self.cAxis.setRange(0, 1/200**2)
        self.cAxis.setTickCount(9)
        self.chart.addAxis(self.cAxis, QtCore.Qt.AlignLeft)
        self.lcrSeries.attachAxis(self.cAxis)

        self.vAxis = QtChart.QValueAxis()
        self.vAxis.setTitleText("Voltage")
        self.vAxis.setLabelFormat("%g V")
        self.vAxis.setRange(0, 200)
        self.vAxis.setTickCount(9)
        self.chart.addAxis(self.vAxis, QtCore.Qt.AlignBottom)
        self.lcrSeries.attachAxis(self.vAxis)

        self.cLimits = LimitsAggregator(self)
        self.vLimits = LimitsAggregator(self)

        self.series['lcr'] = self.lcrSeries

    def fit(self):
        if self.chart.isZoomed():
            return
        minimum = self.vLimits.minimum()
        maximum = self.vLimits.maximum()
        self.vAxis.setReverse(minimum > maximum)
        minimum, maximum = sorted((minimum, maximum))
        self.vAxis.setRange(minimum, maximum)
        self.cAxis.setRange(self.cLimits.minimum(), self.cLimits.maximum())
        self.cAxis.applyNiceNumbers()
        self.cAxis.setTickCount(9)

    def clear(self) -> None:
        super().clear()
        self.cLimits.clear()
        self.vLimits.clear()

    def append(self, name, x, y):
        series = self.series.get(name)
        if series is not None:
            series.append(x, y)
            self.cLimits.append(y)
            self.vLimits.append(x)
            self.fit()
