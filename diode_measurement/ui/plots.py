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
        self.iAxis.setRange(0, 200)
        self.iAxis.hide()
        self.chart.addAxis(self.iAxis, QtCore.Qt.AlignLeft)
        self.smuSeries.attachAxis(self.iAxis)
        self.elmSeries.attachAxis(self.iAxis)

        self.iDynamicAxis = QtChart.QValueAxis()
        self.iDynamicAxis.setTitleText("Current")
        self.iDynamicAxis.setRange(0, 1)
        self.iDynamicAxis.setTickCount(9)
        self.chart.addAxis(self.iDynamicAxis, QtCore.Qt.AlignLeft)
        def updateDynamicAxis(minimum, maximum):
            value = max(abs(minimum), abs(maximum))
            scale, prefix, _ = auto_scale(value)
            self.iDynamicAxis.setRange(minimum * (1 / scale), maximum * (1 / scale))
            self.iDynamicAxis.setLabelFormat(f"%g {prefix}A")
        self.iAxis.rangeChanged.connect(updateDynamicAxis)
        self.iAxis.setRange(0, 0.0000002)

        self.vAxis = QtChart.QValueAxis()
        self.vAxis.setTitleText("Voltage")
        self.vAxis.setLabelFormat("%g V")
        self.vAxis.setRange(-100, +100)
        self.chart.addAxis(self.vAxis, QtCore.Qt.AlignBottom)
        self.smuSeries.attachAxis(self.vAxis)
        self.elmSeries.attachAxis(self.vAxis)

        self.iMin = 0
        self.iMax = 0

        self.series['smu'] = self.smuSeries
        self.series['elm'] = self.elmSeries

    def updateLimits(self, x, y):
        if max(self.smuSeries.count(), self.elmSeries.count()) > 1:
            self.iMin = min(self.iMin, y)
            self.iMax = max(self.iMax, y)
        else:
            self.iMin = y
            self.iMax = y

    def fit(self):
        if self.chart.isZoomed():
            return
        self.vAxis.setReverse(self.isReverse())
        minimum = []
        maximum = []
        for series in self.series.values():
            if series.count():
                minimum.append(series.at(0).x())
                maximum.append(series.at(series.count() - 1).x())
        minimum = min(minimum)
        maximum = max(maximum)
        if self.isReverse():
            minimum, maximum = maximum, minimum
        self.vAxis.setRange(minimum, maximum)
        if self.iMin == self.iMax:
            self.iAxis.setRange(self.iMin, self.iMax + 0.1)
        else:
            self.iAxis.setRange(self.iMin, self.iMax)
        self.iAxis.applyNiceNumbers()

    def append(self, name, x, y):
        series = self.series.get(name)
        if series is not None:
            series.append(x, y)
            self.updateLimits(x, y)
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

        self.iDynamicAxis = QtChart.QValueAxis()
        self.iDynamicAxis.setTitleText("Current")
        self.iDynamicAxis.setRange(0, 1)
        self.iDynamicAxis.setTickCount(9)
        self.chart.addAxis(self.iDynamicAxis, QtCore.Qt.AlignLeft)
        def updateDynamicAxis(minimum, maximum):
            value = max(abs(minimum), abs(maximum))
            scale, prefix, _ = auto_scale(value)
            self.iDynamicAxis.setRange(minimum * (1/scale), maximum * (1/scale))
            self.iDynamicAxis.setLabelFormat(f"%g {prefix}A")
        self.iAxis.rangeChanged.connect(updateDynamicAxis)
        self.iAxis.setRange(0, 0.0000002)

        self.tAxis = QtChart.QDateTimeAxis()
        self.tAxis.setTitleText("Time")
        self.tAxis.setTickCount(3)
        self.chart.addAxis(self.tAxis, QtCore.Qt.AlignBottom)
        self.smuSeries.attachAxis(self.tAxis)
        self.elmSeries.attachAxis(self.tAxis)

        self.iMin = 0
        self.iMax = 0

        self.series['smu'] = self.smuSeries
        self.series['elm'] = self.elmSeries

    def updateLimits(self, x, y):
        if max(self.smuSeries.count(), self.elmSeries.count()) > 1:
            self.iMin = min(self.iMin, y)
            self.iMax = max(self.iMax, y)
        else:
            self.iMin = y
            self.iMax = y

    def fit(self, x, y):
        if self.chart.isZoomed(): return
        minimum = []
        for series in self.series.values():
            if series.count():
                minimum.append(series.at(0).x())
        t0 = QtCore.QDateTime.fromMSecsSinceEpoch(min(minimum))
        t1 = QtCore.QDateTime.fromMSecsSinceEpoch(x * 1e3)
        self.tAxis.setRange(t0, t1)
        self.iMin = min(self.iMin, y)
        self.iMax = max(self.iMax, y)
        if self.iMin == self.iMax:
            self.iAxis.setRange(self.iMin, self.iMax + 0.1)
        else:
            self.iAxis.setRange(self.iMin, self.iMax)
        self.iAxis.applyNiceNumbers()

    def append(self, name, x, y):
        series = self.series.get(name)
        if series is not None:
            series.append(QtCore.QPointF(x * 1e3, y))
            if series.count() > self.MAX_POINTS:
                series.remove(0)
            self.updateLimits(x, y)
            self.fit(x, y)

class CVPlotWidget(PlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart.setTitle("C vs. V")

        self.lcrSeries = QtChart.QLineSeries()
        self.lcrSeries.setName("LCR")
        self.lcrSeries.setColor(QtCore.Qt.magenta)
        self.chart.addSeries(self.lcrSeries)

        self.cAxis = QtChart.QValueAxis()
        self.cAxis.setTitleText("Capacitance")
        self.cAxis.setLabelFormat("%g pF")
        self.cAxis.setRange(0, 200)
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

        self.cMin = 0
        self.cMax = 0

        self.series['lcr'] = self.lcrSeries

    def fit(self, x, y):
        if self.chart.isZoomed(): return
        minimum, maximum = min(series.at(0).x() for series in self.chart.series() if series.count()), x
        self.vAxis.setReverse(minimum > maximum)
        minimum, maximum = sorted((minimum, maximum))
        self.vAxis.setRange(minimum, maximum)
        self.cMin = min(self.cMin, y)
        self.cMax = max(self.cMax, y)
        self.cAxis.setRange(self.cMin, self.cMax)
        self.cAxis.applyNiceNumbers()
        self.cAxis.setTickCount(7)

    def append(self, name, x, y):
        series = self.series.get(name)
        if series is not None:
            series.append(x, y)
            self.fit(x, y)

class CV2PlotWidget(CVPlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart.setTitle("1/C^2 vs. V")
        self.cAxis.setTitleText("Capacitance [1/pF^2]")
        self.cAxis.setLabelFormat("%g")
        self.cAxis.setRange(0, 1/200**2)
        self.vAxis.setTitleText("Voltage")
        self.vAxis.setLabelFormat("%.3g V")
