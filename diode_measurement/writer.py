import csv
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
                safe_format(reading.get('i_smu'), '+.3E'),
                safe_format(reading.get('i_elm'), '+.3E'),
            ]))
            self.measurement.itReading.connect(lambda reading: self.write_continuous_row([
                safe_format(reading.get('timestamp'), '.2f'),
                safe_format(reading.get('voltage'), '+.3E'),
                safe_format(reading.get('i_smu'), '+.3E'),
                safe_format(reading.get('i_elm'), '+.3E'),
            ]))
        elif measurement_type == 'cv':
            self.measurement.cvReading.connect(lambda reading: self.write_row([
                safe_format(reading.get('timestamp'), '.2f'),
                safe_format(reading.get('voltage'), '+.3E'),
                safe_format(reading.get('i_smu'), '+.3E'),
                safe_format(reading.get('c_lcr'), '+.3E'),
                safe_format(reading.get('c_lcr_2'), '+.3E')
            ]))
        self.fp = fp
        self._writer = csv.writer(self.fp, delimiter='\t')

    def flush(self):
        self.fp.flush()

    def write_meta(self):
        self.write_tag("sample", self.measurement.state.get('sample'))
        self.write_tag("measurement_type", self.measurement.state.get('measurement_type'))
        self.write_tag("voltage_begin[V]", safe_format(self.measurement.state.get('voltage_begin'), '+.3E'))
        self.write_tag("voltage_end[V]", safe_format(self.measurement.state.get('voltage_end'), '+.3E'))
        self.write_tag("voltage_step[V]", safe_format(self.measurement.state.get('voltage_step'), '+.3E'))
        self.write_tag("waiting_time[s]", safe_format(self.measurement.state.get('waiting_time'), '+.3E'))
        self.write_tag("current_compliance[A]", safe_format(self.measurement.state.get('current_compliance'), '+.3E'))
        self.flush()

    def write_tag(self, key, value):
        key = key.strip()
        value = value.strip()
        self._writer.writerow([f"{key}: {value}"])

    def write_header(self, columns):
        self._writer.writerow([])
        self._writer.writerow(columns)

    def write_row(self, items):
        measurement_type = self.measurement.state.get('measurement_type')
        if measurement_type == 'iv':
            if self.current_table != 'ramp':
                self.current_table = 'ramp'
                self.write_header(["timestamp[s]", "voltage[V]", "i_smu[A]", "i_elm[A]"])
            self._writer.writerow(items)
        elif measurement_type == 'cv':
            if self.current_table != 'ramp':
                self.current_table = 'ramp'
                self.write_header(["timestamp[s]", "voltage[V]", "i_smu[A]", "c_lcr[F]", "c_lcr_2[F]"])
            self._writer.writerow(items)
        self.flush()

    def write_continuous_row(self, items):
        if self.current_table != 'continous':
            self.current_table = 'continous'
            self.write_header(["timestamp[s]", "voltage[V]", "i_smu[A]", "i_elm[A]"])
        self._writer.writerow(items)
        self.flush()
