from typing import Any, Dict, List, Optional

from PyQt5 import QtWidgets

from .panels import InstrumentPanel
from .widgets import ResourceWidget

__all__ = ["RoleWidget"]


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
        if isinstance(widget, RoleWidget):
            config.update(widget.config())
        return config

    def setConfig(self, config: Dict[str, Any]) -> None:
        for index in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if isinstance(widget, RoleWidget):
                if widget.model() == self.model():
                    widget.setConfig(config)

    def setLocked(self, state: bool) -> None:
        self.resourceWidget.setLocked(state)
        for widget in self.instrumentPanels():
            widget.setLocked(state)

    def addInstrumentPanel(self, widget: InstrumentPanel) -> None:
        self.resourceWidget.addModel(widget.model())
        self.stackedWidget.addWidget(widget)

    def instrumentPanels(self) -> List[InstrumentPanel]:
        """Return list of registered instrument panels."""
        widgets = []
        for index in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if isinstance(widget, InstrumentPanel):
                widgets.append(widget)
        return widgets

    def findInstrumentPanel(self, model: str) -> Optional[InstrumentPanel]:
        for widget in self.instrumentPanels():
            if model == widget.model():
                return widget
        return None

    def modelChanged(self, model: str) -> None:
        widget = self.findInstrumentPanel(model)
        if widget is None:
            self.stackedWidget.setCurrentWidget(self.emptyWidget)
        else:
            self.stackedWidget.setCurrentWidget(widget)
