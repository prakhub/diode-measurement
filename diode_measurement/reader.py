import re
import csv

from .utils import ureg

__all__ = ['Reader']

class Reader:

    def __init__(self, fp):
        self.fp = fp

    def read_meta(self):
        meta = {}
        for line in self.fp:
            line = line.strip()
            if not line:
                break
            m = re.match(r'(\w+)(?:\[(\w+)\])?\:\s*(.*)\s*', line)
            if not m:
                raise RuntimeError(f"Invalid meta entry: {line}")
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
        def source():
            for line in self.fp:
                line = line.strip()
                if not line:
                    break
                yield line
        reader = csv.DictReader(source(), delimiter='\t')
        data = []
        for row in reader:
            if not ''.join(row):
                break # newline
            item = {}
            for key, value in row.items():
                # Strip units
                key = key.split('[')[0]
                item[key] = float(value)
            data.append(item)
        return data
