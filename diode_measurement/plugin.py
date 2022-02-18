from typing import List

from PyQt5 import QtCore

__all__ = ['Plugin', 'PluginRegistryMixin']


class Plugin(QtCore.QObject):
    """Base class for plugins."""

    def install(self, context):
        pass

    def uninstall(self, context):
        pass


class PluginRegistryMixin:
    """Mixin class for handling plugins."""

    __plugins: List[Plugin] = []

    def installPlugin(self, plugin: Plugin) -> None:
        """Install a plugin."""
        self.__plugins.append(plugin)
        plugin.install(self)

    def installedPlugins(self) -> List[Plugin]:
        """Return list of installed plugins."""
        return [plugin for plugin in self.__plugins]

    def uninstallPlugins(self)-> None:
        """Uninstall all plugins."""
        for plugin in self.__plugins:
            plugin.uninstall(self)
