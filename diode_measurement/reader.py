import re
import csv

from .utils import ureg

__all__ = ['Reader']

class Reader:

    def __init__(self, fp):
        self.fp = fp

    def block(self):
        """Return a block of lines, stopping at an empty line."""
        for line in self.fp:
            line = line.decode().strip()
            if not line:
                break
            yield line

    def read_meta(self):
        r = csv.reader(self.block())
        meta = {}
        for row in r:
            if not row:
                break
            m = re.match(r'(\w+)(?:\[(\w+)\])?\:\s*(.*)\s*', row[0])
            if not m:
                raise RuntimeError(f"Invalid meta entry: {row[0]}")
            key = m.group(1)
            if key in meta:
                raise RuntimeError(f"Duplicate meta entry: {key}")
            unit = m.group(2)
            value = m.group(3)
            if unit:
                value = (float(value) * ureg(unit)).m
            meta[key] = value
        return meta

    def read_data(self):
        reader = csv.reader(self.block(), delimiter='\t')
        for row in reader:
            header = [key.split('[')[0] for key in row]
            break
        data = []
        for row in reader:
            if not row:
                break
            values = [float(value) for value in row]
            data.append(dict(zip(header, values)))
        return data
