from PyQt5 import QtCore
from PyQt5 import QtWidgets

from .widgets import ResourceWidget

__all__ = ['RoleWidget']


class RoleWidget(QtWidgets.QWidget):

    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setName(name)

        self.resourceWidget = ResourceWidget()
        self.resourceWidget.modelChanged.connect(self.modelChanged)

        self.emptyWidget = QtWidgets.QWidget()
        self.stackedWidget = QtWidgets.QStackedWidget()
        self.stackedWidget.addWidget(self.emptyWidget)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.resourceWidget)
        layout.addWidget(self.stackedWidget)
        layout.addStretch()

    def name(self):
        return self.property("name")

    def setName(self, name):
        self.setProperty("name", name)

    def model(self):
        return self.resourceWidget.model()

    def setModel(self, model):
        self.resourceWidget.setModel(model)

    def resourceName(self):
        return self.resourceWidget.resourceName()

    def setResourceName(self, resource):
        self.resourceWidget.setResourceName(resource)

    def termination(self):
        return self.resourceWidget.termination()

    def setTermination(self, termination):
        self.resourceWidget.setTermination(termination)

    def timeout(self):
        return self.resourceWidget.timeout()

    def setTimeout(self, timeout):
        self.resourceWidget.setTimeout(timeout)

    def config(self):
        config = {}
        # config["model"] = self.resourceWidget.model()
        # config["resource_name"] = self.resourceWidget.resourceName()
        widget = self.stackedWidget.currentWidget()
        if widget is not self.emptyWidget:
            config.update(widget.config())
        return config

    def setConfig(self, config):
        for index in range(1, self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if widget is not self.emptyWidget:
                if widget.model() == self.model():
                    widget.setConfig(config)

    def lock(self):
        self.resourceWidget.lock()
        for index in range(1, self.stackedWidget.count()):
            self.stackedWidget.widget(index).lock()

    def unlock(self):
        self.resourceWidget.unlock()
        for index in range(1, self.stackedWidget.count()):
            self.stackedWidget.widget(index).unlock()

    def addInstrument(self, widget):
        self.resourceWidget.addModel(widget.model())
        self.stackedWidget.addWidget(widget)

    @QtCore.pyqtSlot(str)
    def modelChanged(self, model):
        for index in range(1, self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if widget.model() == model:
                self.stackedWidget.setCurrentWidget(widget)
                return
        self.stackedWidget.setCurrentWidget(self.emptyWidget)
