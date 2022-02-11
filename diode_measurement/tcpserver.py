import jsonrpc
import logging
import math
import socketserver
import threading
import time

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from .plugin import Plugin

__all__ = ['TCPServerPlugin']

logger = logging.getLogger(__name__)


def isfinite(value: object) -> object:
    return isinstance(value, float) and not math.isfinite(value)


def json_dict(d: dict) -> dict:
    """Replace non-finite floats (nan, +inf, -inf) with `None` to be converted to `null` in JSON."""
    return {k: (None if isfinite(v) else v) for k, v in d.items()}


class RPCHandler:

    def __init__(self, controller):
        self.controller = controller
        self.dispatcher = jsonrpc.Dispatcher()
        self.dispatcher['start'] = self.onStart
        self.dispatcher['stop'] = self.onStop
        self.dispatcher['change_voltage'] = self.onChangeVoltage
        self.dispatcher['state'] = self.onState
        self.manager = jsonrpc.JSONRPCResponseManager()

    def __call__(self):
        return self.controller()

    def handle(self, request):
        return self.manager.handle(request, self.dispatcher)

    def onStart(self):
        self.controller.started.emit()

    def onStop(self):
        self.controller.stopped.emit()

    def onChangeVoltage(self, end_voltage, step_voltage=1.0, waiting_time=1.0):
        self.controller.changeVoltageController.onRequestChangeVoltage(end_voltage, step_voltage, waiting_time)

    def onState(self):
        return json_dict(self.controller.snapshot())


class TCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip().decode('utf-8')
        logger.info("%s wrote: %s", self.client_address[0], self.data)
        response = self.server.rpcHandler.handle(self.data)
        if response:
            data = response.json.encode('utf-8')
            logger.info("%s returned: %s", self.client_address[0], data)
            self.request.sendall(data)


class TCPServer(socketserver.TCPServer):

    allow_reuse_address = True


class RPCWidget(QtWidgets.QWidget):

    reconnectSignal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RPC")

        # Widgets

        self.rpcGroupBox = QtWidgets.QGroupBox("JSON-RPC Server")

        self.stateLabel = QtWidgets.QLabel()
        self.stateLabel.setText("Disconnected")

        self.hostnameLineEdit = QtWidgets.QLineEdit("localhost")

        self.portSpinBox = QtWidgets.QSpinBox()
        self.portSpinBox.setRange(0, 999999)
        self.portSpinBox.setValue(8000)

        self.autoConnectCheckBox = QtWidgets.QCheckBox("Auto Connect")
        self.autoConnectCheckBox.setToolTip("Connect server on startup")
        self.autoConnectCheckBox.setStatusTip("Connect server on startup")

        self.reconnectButton = QtWidgets.QToolButton()
        self.reconnectButton.setText("Connect")

        # Layouts

        formLayout = QtWidgets.QFormLayout(self.rpcGroupBox)
        formLayout.addRow("State", self.stateLabel)
        formLayout.addRow("Hostname", self.hostnameLineEdit)
        formLayout.addRow("Port", self.portSpinBox)
        formLayout.addRow("", self.autoConnectCheckBox)
        formLayout.addRow("", self.reconnectButton)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.rpcGroupBox)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 2)

        # Connections

        self.reconnectButton.clicked.connect(lambda: self.reconnectSignal.emit())
        self.reconnectButton.clicked.connect(lambda: self.reconnectButton.setEnabled(False))
        self.reconnectButton.clicked.connect(lambda: self.setState("Connecting..."))
        self.portSpinBox.editingFinished.connect(lambda: self.reconnectButton.setEnabled(True))
        self.hostnameLineEdit.editingFinished.connect(lambda: self.reconnectButton.setEnabled(True))

    def isServerEnabled(self) -> bool:
        return self.autoConnectCheckBox.isChecked()

    def setServerEnabled(self, enabled: bool) -> None:
        self.autoConnectCheckBox.setChecked(enabled)

    def setConnected(self, connected: bool)-> None:
        self.reconnectButton.setEnabled(True)
        self.reconnectButton.setText("Disconnect" if connected else "Connect")
        self.portSpinBox.setEnabled(not connected)
        self.hostnameLineEdit.setEnabled(not connected)
        self.setState("Connected" if connected else "Disconnected")

    def hostname(self) -> str:
        return self.hostnameLineEdit.text().strip()

    def setHostname(self, hostname: str) -> None:
         self.hostnameLineEdit.setText(hostname)

    def port(self) -> int:
        return self.portSpinBox.value()

    def setPort(self, port: int) -> None:
         self.portSpinBox.setValue(port)

    def setState(self, text: str) -> None:
        self.stateLabel.setText(text)


class TCPServerPlugin(Plugin):

    startRequest = QtCore.pyqtSignal()
    stopRequest = QtCore.pyqtSignal()
    itChangeVoltage = QtCore.pyqtSignal(float, float, float)
    connected = QtCore.pyqtSignal(bool)
    failed = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = threading.Thread(target=self.run)
        self._q = []
        self._enabled = threading.Event()
        self._reconnect = False

    def install(self, context):
        self.failed.connect(context.onFailed)
        self._installTab(context)
        self.rpcHandler = RPCHandler(context)
        self.startRequest.connect(context.started.emit)
        self.stopRequest.connect(context.stopped.emit)
        self.itChangeVoltage.connect(context.changeVoltageController.onRequestChangeVoltage)
        self.loadSettings()
        self._startServer()

    def shutdown(self, context):
        self.failed.disconnect(context.onFailed)
        self._enabled.clear()
        while self._q:
            self._q.pop()()
        self._context = None
        self.storeSettings()

    def loadSettings(self):
        settings = QtCore.QSettings()
        enabled = settings.value("tcpServer/enabled", False, bool)
        hostname = settings.value("tcpServer/hostname", "", str)
        port = settings.value("tcpServer/port", 8000, int)
        self.rpcWidget.setServerEnabled(enabled)
        self.rpcWidget.setHostname(hostname)
        self.rpcWidget.setPort(port)

    def storeSettings(self):
        settings = QtCore.QSettings()
        enabled = self.rpcWidget.isServerEnabled()
        hostname = self.rpcWidget.hostname()
        port = self.rpcWidget.port()
        settings.setValue("tcpServer/enabled", enabled)
        settings.setValue("tcpServer/hostname", hostname)
        settings.setValue("tcpServer/port", port)

    def requestReconnect(self):
        while self._q:
            self._q.pop()()
        self._reconnect = True

    def join(self):
        self._thread.join()

    def _installTab(self, context):
        self.rpcWidget = RPCWidget()
        self.connected.connect(lambda state: self.rpcWidget.setConnected(state))
        self.rpcWidget.reconnectSignal.connect(lambda: self.requestReconnect())
        context.view.controlTabWidget.insertTab(1000, self.rpcWidget, self.rpcWidget.windowTitle())

    def _startServer(self):
        self._enabled.set()
        self._thread.start()

    def _setupServer(self, server):
        self._q.append(server.shutdown)
        server.rpcHandler = self.rpcHandler
        server.startRequest = self.startRequest
        server.stopRequest = self.stopRequest
        server.itChangeVoltage = self.itChangeVoltage

    def run(self):
        self._reconnect = self.rpcWidget.isServerEnabled()
        while self._enabled.is_set():
            if self._reconnect:
                hostname = self.rpcWidget.hostname()
                port = self.rpcWidget.port()
                logger.info("TCP connect %s:%s", hostname, port)
                try:
                    with TCPServer((hostname, port), TCPHandler) as server:
                        self.connected.emit(True)
                        self._setupServer(server)
                        server.serve_forever()
                except Exception as exc:
                    logger.exception(exc)
                    self.failed.emit(exc)
                finally:
                    self._reconnect = False
                    logger.info("TCP disconnect %s:%s", hostname, port)
                    self.connected.emit(False)
                    self._q.clear()
                    time.sleep(.50)
            else:
                time.sleep(.50)
