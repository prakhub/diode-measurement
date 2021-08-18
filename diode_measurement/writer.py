import os

def safe_format(value, format_spec=''):
    try:
        return format(value, format_spec)
    except:
        return format(float('nan'))

class Writer:

    def __init__(self, measurement, fp):
        self.measurement = measurement
        self.current_table = None
        self.measurement.started.connect(self.write_meta)
        measurement_type = measurement.state.get('measurement_type')
        if measurement_type == 'iv':
            self.measurement.ivReading.connect(lambda reading: self.write_row([
                safe_format(reading.get('timestamp'), '.2f'),
                safe_format(reading.get('voltage'), '+.3E'),
                safe_format(reading.get('i_smu', 0.0), '+.3E'),
                safe_format(reading.get('i_elm', 0.0), '+.3E'),
            ]))
            self.measurement.itReading.connect(lambda reading: self.write_continuous_row([
                safe_format(reading.get('timestamp'), '.2f'),
                safe_format(reading.get('i_smu'), '+.3E'),
            ]))
        elif measurement_type == 'cv':
            self.measurement.cvReading.connect(lambda reading: self.write_row([
                safe_format(reading.get('timestamp'), '.2f'),
                safe_format(reading.get('voltage'), '+.3E'),
                safe_format(reading.get('c_lcr'), '+.3E')
            ]))
        self.fp = fp

    def write_meta(self):
        self.write_tag("sample", self.measurement.state.get('sample'))
        self.write_tag("measurement_type", self.measurement.state.get('measurement_type'))
        self.write_tag("voltage_begin[V]", safe_format(self.measurement.state.get('voltage_begin'), '+.3E'))
        self.write_tag("voltage_end[V]", safe_format(self.measurement.state.get('voltage_end'), '+.3E'))
        self.write_tag("voltage_step[V]", safe_format(self.measurement.state.get('voltage_step'), '+.3E'))
        self.write_tag("waiting_time[s]", safe_format(self.measurement.state.get('waiting_time'), '+.3E'))
        self.write_tag("current_compliance[A]", safe_format(self.measurement.state.get('current_compliance'), '+.3E'))

    def write_line(self, line):
        self.fp.write(f"{line}\r\n")

    def write_tag(self, key, value):
        key = key.strip()
        value = value.strip()
        self.write_line(f"{key}: {value}")

    def write_header(self, columns):
        self.write_line("")
        self.write_line("\t".join(columns))

    def write_row(self, items):
        measurement_type = self.measurement.state.get('measurement_type')
        if measurement_type == 'iv':
            if self.current_table != 'ramp':
                self.current_table = 'ramp'
                self.write_header(["timestamp[s]", "voltage[V]", "i_smu[A]", "i_elm[A]"])
            self.write_line("\t".join([format(item) for item in items]))
        elif measurement_type == 'cv':
            if self.current_table != 'ramp':
                self.current_table = 'ramp'
                self.write_header(["timestamp[s]", "voltage[V]", "c_lcr[F]"])
            self.write_line("\t".join([format(item) for item in items]))

    def write_continuous_row(self, items):
        if self.current_table != 'continous':
            self.current_table = 'continous'
            self.write_header(["timestamp[s]", "i_smu[A]"])
        self.write_line("\t".join([format(item) for item in items]))
