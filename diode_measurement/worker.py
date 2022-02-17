import logging
from threading import Event, Thread
from queue import Queue, Empty

from PyQt5 import QtCore

__all__ = ['Worker']

logger = logging.getLogger(__name__)


class Worker(QtCore.QObject):

    failed = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._shutdownEvent: Event = Event()
        self._queue: Queue = Queue()
        self._thread: Thread = Thread(target=self.eventLoop)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._shutdownEvent.set()

    def request(self, callback) -> None:
        self._queue.put(callback)

    def handleRequest(self) -> None:
        try:
            self._queue.get(timeout=0.25)()
        except Empty:
            pass

    def eventLoop(self) -> None:
        while not self._shutdownEvent.is_set():
            try:
                self.handleRequest()
            except Exception as exc:
                logger.exception(exc)
                self.failed.emit(exc)
            finally:
                self.finished.emit()
