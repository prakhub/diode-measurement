from typing import Any, List

__all__ = ["Plugin", "PluginRegistry"]


class Plugin:
    """Base class for plugins."""

    def install(self, context: Any) -> None:
        ...

    def uninstall(self, context: Any) -> None:
        ...


class PluginRegistry:
    """Manager class for handling plugins."""

    def __init__(self, context: Any) -> None:
        self._context: Any = context
        self._plugins: List[Plugin] = []

    def install(self, plugin: Plugin) -> None:
        """Install a plugin."""
        self._plugins.append(plugin)
        plugin.install(self._context)

    @property
    def plugins(self) -> List[Plugin]:
        """Return list of installed plugins."""
        return [plugin for plugin in self._plugins]

    def uninstall(self) -> None:
        """Uninstall all plugins."""
        for plugin in self._plugins[:]:
            plugin.uninstall(self._context)
            self._plugins.remove(plugin)
