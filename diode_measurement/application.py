import logging
import sys
import os

from PyQt5 import QtCore, QtGui, QtWidgets

from . import __version__
from .controller import Controller
from .ui.mainwindow import MainWindow
from .plugins import PluginRegistry
from .plugins.tcpserver import TCPServerPlugin
from .plugins.screenshot import ScreenshotPlugin

__all__ = ["Application"]

logger = logging.getLogger(__name__)

PACKAGE_PATH = os.path.realpath(os.path.dirname(__file__))
ASSETS_PATH = os.path.join(PACKAGE_PATH, "assets")


class Application(QtWidgets.QApplication):

    def __init__(self):
        super().__init__(sys.argv)
        self.setApplicationName("diode-measurement")
        self.setApplicationVersion(__version__)
        self.setApplicationDisplayName(f"Diode Measurement {__version__}")
        self.setOrganizationName("HEPHY")
        self.setOrganizationDomain("hephy.at")

        icon = QtGui.QIcon(os.path.join(ASSETS_PATH, "icons", "diode-measurement.svg"))
        self.setWindowIcon(icon)

    def bootstrap(self):
        # Initialize settings
        QtCore.QSettings()

        window = MainWindow()

        logger.info("Diode Measurement, version %s", __version__)

        controller = Controller(window)
        controller.loadSettings()

        plugins = PluginRegistry(controller)
        plugins.install(TCPServerPlugin())
        plugins.install(ScreenshotPlugin())

        self.aboutToQuit.connect(lambda: controller.storeSettings())
        window.show()

        # Interrupt timer
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(250)

        self.exec()

        controller.shutdown()
        plugins.uninstall()
