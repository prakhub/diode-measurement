from diode_measurement.plugin import Plugin


class TestPlugin:

    def test_plugin(self):
        context = {}
        plugin = Plugin()
        plugin.install(context)
        plugin.uninstall(context)
