from diode_measurement.plugins import Plugin


def test_plugin():
    context = {}
    plugin = Plugin()
    plugin.install(context)
    plugin.uninstall(context)
