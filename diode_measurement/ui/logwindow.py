import html
import logging
import threading

from typing import Callable

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

__all__ = ["LogWindow", "LogWidget"]


class LogHandler(logging.Handler):

    def __init__(self, callback: Callable) -> None:
        super().__init__()
        self._callback = callback

    def emit(self, record):
        self._callback(record)


class LogWidget(QtWidgets.QTextEdit):

    MaximumEntries: int = 1024 * 1024
    """Maximum number of visible log entries."""

    message = QtCore.pyqtSignal(object)

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.document().setMaximumBlockCount(type(self).MaximumEntries)
        self.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.handler = LogHandler(self.message.emit)
        self.setLevel(logging.INFO)
        self.message.connect(self.appendRecord)
        self.recordCache = []
        self.recordCacheLock = threading.RLock()
        self.recordTimer = QtCore.QTimer()
        self.recordTimer.timeout.connect(self.applyCachedRecords)
        self.recordTimer.start(250)

    def setLevel(self, level: int) -> None:
        """Set log level of widget."""
        self.handler.setLevel(level)

    def addLogger(self, logger: logging.Logger) -> None:
        """Add logger to widget."""
        logger.addHandler(self.handler)

    def removeLogger(self, logger: logging.Logger) -> None:
        """Remove logger from widget."""
        logger.removeHandler(self.handler)

    def appendRecord(self, record: logging.LogRecord) -> None:
        """Append log record to log cache."""
        with self.recordCacheLock:
            self.recordCache.append(record)

    def applyCachedRecords(self) -> None:
        """Append cached log records to log widget."""
        records = []
        with self.recordCacheLock:
            records = self.recordCache[:]
            self.recordCache.clear()
        if not records:
            return
        # Get current scrollbar position
        scrollbar = self.verticalScrollBar()
        position = scrollbar.value()
        # Lock to current position or to bottom
        lock = False
        if position + 1 >= scrollbar.maximum():
            lock = True
        # Append foramtted log messages
        for record in records:
            self.append(self.formatRecord(record))
        # Scroll to bottom
        if lock:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(position)

    def ensureRecentRecordsVisible(self) -> None:
        scrollbar.setValue(scrollbar.maximum())

    @classmethod
    def formatTime(cls, seconds: float) -> str:
        """Format timestamp for log record."""
        dt = QtCore.QDateTime.fromMSecsSinceEpoch(int(seconds * 1e3))
        return dt.toString("yyyy-MM-dd hh:mm:ss")

    @classmethod
    def formatRecord(cls, record: logging.LogRecord) -> str:
        """Format colored log record."""
        if record.levelno >= logging.ERROR:
            color = "red"
        elif record.levelno >= logging.WARNING:
            color = "orange"
        elif record.levelno >= logging.INFO:
            color = "inherit"
        elif record.levelno >= logging.DEBUG:
            color = "darkgrey"
        else:
            color = "inherit"
        style = f"white-space:pre;color:{color};margin:0"
        timestamp = cls.formatTime(record.created)
        message = "{}\t{}\t{}".format(timestamp, record.levelname, record.getMessage())
        # Escape to HTML
        message = html.escape(message)
        return f"<span style=\"{style}\">{message}</span>"


class LogWindow(QtWidgets.QWidget):

    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Logging"))

        self.logHeader = QtWidgets.QLabel()
        self.logHeader.setTextFormat(QtCore.Qt.RichText)
        self.logHeader.setText("<span style=\"white-space:pre\">Time\t\tLevel\tMessage</span>")

        self.logWidget = LogWidget()

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(self.buttonBox.Close)
        self.buttonBox.rejected.connect(lambda: self.hide())

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.logHeader)
        layout.addWidget(self.logWidget)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def setLevel(self, level: int) -> None:
        """Set log level of widget."""
        self.logWidget.setLevel(level)

    def addLogger(self, logger: logging.Logger) -> None:
        """Add logger to widget."""
        self.logWidget.addLogger(logger)

    def removeLogger(self, logger: logging.Logger) -> None:
        """Remove logger from widget."""
        self.logWidget.removeLogger(logger)

    def clear(self) -> None:
        """Clear log history."""
        self.logWidget.clear()
