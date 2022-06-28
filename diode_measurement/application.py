import logging
import sys
import os

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import __version__
from .controller import Controller
from .ui.mainwindow import MainWindow
from .tcpserver import TCPServerPlugin

logger = logging.getLogger(__name__)

PACKAGE_PATH = os.path.realpath(os.path.dirname(__file__))
ASSETS_PATH = os.path.join(PACKAGE_ROOT, "assets")


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
        controller.installPlugin(TCPServerPlugin())
        controller.loadSettings()

        self.aboutToQuit.connect(lambda: controller.storeSettings())
        window.show()

        # Interrupt timer
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(250)

        self.exec()

        controller.shutdown()
