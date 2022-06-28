from PyQt5 import QtWidgets

from typing import Any, Dict

from .panels import InstrumentPanel
from .widgets import ResourceWidget

__all__ = ['RoleWidget']


class RoleWidget(QtWidgets.QWidget):

    def __init__(self, name, parent: QtWidgets.QWidget = None) -> None:
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
        layout.setStretch(0, 1)
        layout.setStretch(1, 2)

    def name(self) -> str:
        return self.property("name")

    def setName(self, name: str) -> None:
        self.setProperty("name", name)

    def model(self) -> str:
        return self.resourceWidget.model()

    def setModel(self, model: str) -> None:
        self.resourceWidget.setModel(model)

    def resourceName(self) -> str:
        return self.resourceWidget.resourceName()

    def setResourceName(self, resource: str) -> None:
        self.resourceWidget.setResourceName(resource)

    def termination(self) -> str:
        return self.resourceWidget.termination()

    def setTermination(self, termination: str) -> None:
        self.resourceWidget.setTermination(termination)

    def timeout(self) -> float:
        return self.resourceWidget.timeout()

    def setTimeout(self, timeout: float) -> None:
        self.resourceWidget.setTimeout(timeout)

    def config(self) -> Dict[str, Any]:
        config = {}
        # config["model"] = self.resourceWidget.model()
        # config["resource_name"] = self.resourceWidget.resourceName()
        widget = self.stackedWidget.currentWidget()
        if widget is not self.emptyWidget:
            config.update(widget.config())
        return config

    def setConfig(self, config: Dict[str, Any]) -> None:
        for index in range(1, self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if widget is not self.emptyWidget:
                if widget.model() == self.model():
                    widget.setConfig(config)

    def setLocked(self, state: bool) -> None:
        self.resourceWidget.setLocked(state)
        for index in range(1, self.stackedWidget.count()):
            self.stackedWidget.widget(index).setLocked(state)

    def addInstrument(self, widget: InstrumentPanel) -> None:
        self.resourceWidget.addModel(widget.model())
        self.stackedWidget.addWidget(widget)

    def modelChanged(self, model: str) -> None:
        for index in range(1, self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if widget.model() == model:
                self.stackedWidget.setCurrentWidget(widget)
                return
        self.stackedWidget.setCurrentWidget(self.emptyWidget)
