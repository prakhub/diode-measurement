import logging
import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import __version__
from .controller import Controller
from .ui.mainwindow import MainWindow

logger = logging.getLogger(__name__)


class Application(QtWidgets.QApplication):

    def __init__(self):
        super().__init__(sys.argv)
        self.setApplicationName("diode-measurement")
        self.setApplicationVersion(__version__)
        self.setApplicationDisplayName(f"Diode Measurement {__version__}")
        self.setOrganizationName("HEPHY")
        self.setOrganizationDomain("hephy.at")

    def bootstrap(self):
        # Initialize settings
        QtCore.QSettings()

        window = MainWindow()

        logger.info("Diode Measurement, version %s", __version__)

        controller = Controller(window)
        controller.loadSettings()
        self.aboutToQuit.connect(lambda: controller.storeSettings())
        window.show()

        # Interrupt timer
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(250)

        return self.exec()
