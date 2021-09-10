# Diode Measurement

IV/CV measurements for silicon sensors.

## Install

On Windows download a pre-built executable from the release section and run it.

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

## Supported Instruments

Source Meter Units

- Keithley K237
- Keithley K2410
- Keithley K2470
- Keithley K2657A

Electro Meter

- Keithley K6514
- Keithley K6517B

LCR Meter

- Keithley K595
- Keysight E4980A

## Setup

To interface instruments using a GPIB interface the NI-VISA drivers need to be 
installed. Interfacing instruments using TCPIP, USB or Serial port is supported
out of the box by using PyVISA-py, pyusb and pyserial.

The instrument resource name inputs accept follwing formats:

|Format|Example|Result|
|:-----|:------|:-----|
|&lt;n&gt;|16|GPIB::16::INSTR|
|&lt;ip&gt;:&lt;port&gt;|0.0.0.0:1080|TCPIP::0.0.0.0::1080::SOCKET|
|&lt;host&gt;:&lt;port&gt;|localhost:1080|TCPIP::localhost::1080::SOCKET|
|&lt;visa&gt;|GPIB1::16::INSTR|GPIB1::16::INSTR|
  
## Data formats

The used plain text format consists of a header containing meta data in key and
value pairs and one or more CSV data tables with headers using `\t` separators.

### Synopsis

```
<key>: <value>
...
<<series>[<unit>]\t...>
<<value>\t...>
...
```

### IV

IV measurement data consist of up to two CSV tables with the second (optional)
table containing continuous measurement data.

#### Example

```
sample: Unnamed
measurement_type: iv
voltage_begin[V]: +5.000E+00
voltage_end[V]: -1.000E+01
voltage_step[V]: +1.000E+00
waiting_time[s]: +1.000E-01
current_compliance[A]: +1.000E-06

timestamp[s]	voltage[V]	i_smu[A]	i_elm[A]
1629455368.29	+5.000E+00	+4.261E-08	+3.740E-08
1629455369.71	+4.000E+00	+7.708E-08	+9.495E-08
1629455370.49	+3.000E+00	+3.460E-08	+6.264E-08
...          	...       	...       	...

timestamp[s]	voltage[V]	i_smu[A]	i_elm[A]
1629455385.69	+3.000E+00	+3.996E-04	+7.137E-08
1629455387.65	+3.000E+00	+7.353E-04	+3.079E-08
1629455389.56	+3.000E+00	+9.081E-04	+1.266E-08
...          	...       	...
```

### CV

CV measurement data consist of a single CSV table containing the measurement
data.

#### Example

```
sample: Unnamed
measurement_type: cv
voltage_begin[V]: +5.000E+00
voltage_end[V]: -1.000E+01
voltage_step[V]: +1.000E+00
waiting_time[s]: +1.000E-01
current_compliance[A]: +1.000E-08

timestamp[s]	voltage[V]	i_smu[A]	c_lcr[F]	c_lcr[F]
1629455368.29	+5.000E+00	+4.261E-08	+3.740E-05	7.149E+08
1629455369.71	+4.000E+00	+7.708E-08	+9.495E-05	1.109E+08
1629455370.49	+3.000E+00	+3.460E-08	+6.264E-05	2.549E+08
...          	...       	...       	...       	...
```
