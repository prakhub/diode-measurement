from diode_measurement.plugins import Plugin


class TestPlugin:

    def test_plugin(self):
        context = {}
        plugin = Plugin()
        plugin.install(context)
        plugin.uninstall(context)
