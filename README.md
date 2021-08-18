# Diode Measurement

IV/CV measurements for silicon sensors.

## Build

Building a Windows executable using PyInstaller.

```bash
python -m venv build_env
. build_env/Scripts/activate
pip install -U pip
pip install pyinstaller
python setup.py install
python setup.py test
pyinstaller ./pyinstaller.spec
```
