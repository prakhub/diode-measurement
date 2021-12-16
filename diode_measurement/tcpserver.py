import jsonrpc
import logging
import socketserver
import threading
import time

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from .plugin import Plugin

__all__ = ['TCPServerPlugin']

logger = logging.getLogger(__name__)


class RPCHandler:

    def __init__(self, controller):
        self.controller = controller
        self.dispatcher = jsonrpc.Dispatcher()
        self.dispatcher['start'] = self.on_start
        self.dispatcher['stop'] = self.on_stop
        self.dispatcher['change_voltage'] = self.on_change_voltage
        self.dispatcher['state'] = self.on_state
        self.manager = jsonrpc.JSONRPCResponseManager()

    def __call__(self):
        return self.controller()

    def handle(self, request):
        return self.manager.handle(request, self.dispatcher)

    def on_start(self):
        self.controller.started.emit()

    def on_stop(self):
        self.controller.stopped.emit()

    def on_change_voltage(self, end_voltage, step_voltage=1.0, waiting_time=1.0):
        self.controller.changeVoltageController.onRequestChangeVoltage(end_voltage, step_voltage, waiting_time)

    def on_state(self):
        return self.controller.snapshot()


class TCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip().decode('utf-8')
        logger.info("%s wrote: %s", self.client_address[0], self.data)
        response = self.server.rpcHandler.handle(self.data)
        if response:
            data = response.json.encode('utf-8')
            logger.info("%s returned: %s", self.client_address[0], data)
            self.request.sendall(data)


class _TCPServer(socketserver.TCPServer):

    allow_reuse_address = True


class RPCWidget(QtWidgets.QWidget):

    reconnectSignal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RPC")

        self.rpcGroupBox = QtWidgets.QGroupBox("JSON-RPC Server")

        self.hostnameLineEdit = QtWidgets.QLineEdit("localhost")

        self.portSpinBox = QtWidgets.QSpinBox()
        self.portSpinBox.setRange(0, 999999)
        self.portSpinBox.setValue(8000)

        self.portSpinBox.editingFinished.connect(lambda: self.reconnectSignal.emit())
        self.hostnameLineEdit.editingFinished.connect(lambda: self.reconnectSignal.emit())

        layout = QtWidgets.QFormLayout(self.rpcGroupBox)
        layout.addRow("Hostname", self.hostnameLineEdit)
        layout.addRow("Port", self.portSpinBox)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.rpcGroupBox, 0, 0)

    def hostname(self) -> str:
        return self.hostnameLineEdit.text().strip()

    def setHostname(self, hostname: str) -> None:
         self.hostnameLineEdit.setText(hostname)

    def port(self) -> int:
        return self.portSpinBox.value()

    def setPort(self, port: int) -> None:
         self.portSpinBox.setValue(port)


class TCPServerPlugin(Plugin):

    startRequest = QtCore.pyqtSignal()
    stopRequest = QtCore.pyqtSignal()
    itChangeVoltage = QtCore.pyqtSignal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = threading.Thread(target=self.run)
        self._q = []
        self._enabled = threading.Event()

    def install(self, context):
        self.installTab(context)
        self.rpcHandler = RPCHandler(context)
        self.startRequest.connect(context.started.emit)
        self.stopRequest.connect(context.stopped.emit)
        self.itChangeVoltage.connect(context.changeVoltageController.onRequestChangeVoltage)
        self.loadSettings()
        self.startServer()

    def shutdown(self, context):
        self._enabled.clear()
        while self._q:
            self._q.pop()()
        self._context = None
        self.storeSettings()

    def loadSettings(self):
        settings = QtCore.QSettings()
        hostname = settings.value("tcpServer/hostname", "", str)
        port = settings.value("tcpServer/port", 8000, int)
        self.rpcWidget.setHostname(hostname)
        self.rpcWidget.setPort(port)

    def storeSettings(self):
        settings = QtCore.QSettings()
        hostname = self.rpcWidget.hostname()
        port = self.rpcWidget.port()
        settings.setValue("tcpServer/hostname", hostname)
        settings.setValue("tcpServer/port", port)

    def installTab(self, context):
        self.rpcWidget = RPCWidget()
        self.rpcWidget.reconnectSignal.connect(self.reconnect)
        context.view.controlTabWidget.insertTab(1000, self.rpcWidget, self.rpcWidget.windowTitle())

    def startServer(self):
        self._enabled.set()
        self._thread.start()

    def reconnect(self):
        while self._q:
            self._q.pop()()

    def join(self):
        self._thread.join()

    def run(self):
        while self._enabled.is_set():
            try:
                hostname = self.rpcWidget.hostname()
                port = self.rpcWidget.port()
                logger.info("TCP connect %s:%s", hostname, port)
                with _TCPServer((hostname, port), TCPHandler) as server:
                    self._q.append(server.shutdown)
                    server.rpcHandler = self.rpcHandler
                    server.startRequest = self.startRequest
                    server.stopRequest = self.stopRequest
                    server.itChangeVoltage = self.itChangeVoltage
                    server.serve_forever()
            except Exception as exc:
                logger.exception(exc)
            finally:
                self._q.clear()
                time.sleep(.25)
