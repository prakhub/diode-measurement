import time
from typing import Tuple

from .driver import LCRMeter, handle_exception

__all__ = ["K4215"]


class K4215(LCRMeter):

    def __init__(self, resource):
        super().__init__(resource)
        # self.resource.write_termination = "\0"
        # self.resource.read_termination = "\r\n"

    def identity(self) -> str:
        return self._query("*IDN?").strip()

    def reset(self) -> None:
        self._write("*RST")

    def clear(self) -> None:
        # clear buffer
        self._write("BC")

    def next_error(self) -> Tuple[int, str]:

        return 0, "No Error"
        # code, message = self._query(":SYST:ERR?").split(",")
        # code = int(code)
        # message = message.strip().strip('"')
        # return code, message

    def configure(self, options: dict) -> None:
        self._write(":CVU:MODE 0")
        self._enable_bias_tee_dc_voltage()

        # Impedance Type
        self.set_function_impedance_type(2)  # CpRp

        # Aperture
        self.set_aperture()

        # Correction cable length
        self.set_correction()

        voltage = options.get("voltage", 1.0)
        self.set_amplitude_voltage(voltage)

        frequency = options.get("frequency", 100000.0)
        self.set_amplitude_frequency(frequency)

    def set_aci_range(self, level: float) -> None:

        self._write(f":CVU:ACZ:RANGE {level:.3E}")

    def get_output_enabled(self) -> bool:
        return self._query(":CVU:OUTPUT?") == "1"

    def set_output_enabled(self, enabled: bool) -> None:
        value = {False: "0", True: "1"}[enabled]
        self._write(f":CVU:OUTPUT {value}")

    def set_correction(self):
        self._write(":CVU:CORRECT 0,0,0")

    def set_current_compliance_level(self, level: float) -> None:
        raise RuntimeError("current compliance not supported")

    def compliance_tripped(self) -> bool:
        raise RuntimeError("current compliance not supported")

    def measure_i(self) -> float:
        return 0.0

    def measure_iv(self) -> Tuple[float, float]:
        return 0.0, 0.0

    def _fetch(self, timeout=10.0, interval=0.250) -> str:
        threshold = time.time() + timeout
        interval = min(timeout, interval)
        while time.time() < threshold:
            try:
                return self._query(":CVU:MEASZ?")
            except Exception as exc:
                raise RuntimeError(f"Failed to fetch LCR reading: {exc}") from exc
            time.sleep(interval)
        raise RuntimeError(f"LCR reading timeout, exceeded {timeout:G} s")

    def measure_impedance(self) -> Tuple[float, float]:
        result = self._fetch().split(",")
        try:
            return float(result[0]), float(result[1])
        except Exception as exc:
            raise RuntimeError(
                f"Failed to parse impedance reading: {result!r}"
            ) from exc

    def set_function_impedance_type(self, impedance_type: int) -> None:
        # The model:
        # 0: Z, theta
        # 1: R + jx (default)
        # 2: Cp, Gp
        # 3: Cs, Rs
        # 4: Cp, D
        # 5: Cs, D
        # 7: Y, theta
        self._write(f":CVU:MODEL {impedance_type}")

    def set_aperture(self) -> None:
        self._write(":CVU:SPEED 2")
        # self.k4200.write(":CVU:SPEED 3,1,3,10")

        # assert integration_time in ["SHOR", "MED", "LONG"]
        # assert 1 <= averaging_rate <= 128
        # # self._write(f":CVU:SPEED 3,{integration_time},{averaging_rate:d}")

    def set_amplitude_voltage(self, voltage: float) -> None:
        self._write(f":CVU:ACV {voltage:E}")

    def set_amplitude_frequency(self, frequency: float) -> None:
        self._write(f":CVU:FREQ {int(frequency)}")

    @handle_exception
    def _write(self, message):
        self.resource.write(message)
        # self.resource.query("*OPC?")

    @handle_exception
    def _write_nowait(self, message):
        self.resource.write(message)

    @handle_exception
    def _query(self, message):
        return self.resource.query(message).strip()

    # def set_correction_length(self, correction_length: int) -> None:
    #     assert correction_length in [0, 1, 2]
    #     self._write(f":CORR:LENG {correction_length:d}")

    # def set_correction_open_state(self, state: bool) -> None:
    #     self._write(f":CVU:CORRECT {state:d},0,0")

    # def set_correction_short_state(self, state: bool) -> None:
    #     self._write(f":CVU:CORRECT 0,{state:d},0")

    # def set_amplitude_alc(self, enabled: bool) -> None:
    #     self._write(f":AMPL:ALC {enabled:d}")
    # def get_voltage_level(self) -> float:
    #     return float(self._query(":BIAS:VOLT:LEV?"))

    def get_voltage_level(self) -> float:
        return 0.0

    def set_voltage_level(self, level: float) -> None:
        pass
        # self._write(f":BIAS:VOLT:LEV {level:.3E}")

    def set_voltage_range(self, level: float) -> None:
        pass

    def _enable_bias_tee_dc_voltage(self):
        self._write(":CVU:CONFIG:ACVHI 1")
        self._write(":CVU:CONFIG:DCVHI 2")
        self._write(":CVU:DCV:OFFSET -10")
        self._write(":CVU:DCV -10")

    def finalize(self):
        self.reset()

# class K4200:
#     def __init__(self, resource_str="GPIB::17::INSTR"):
#         self.k4200 = Communications(resource_str)
#         self.k4200.connect()

#         self.k4200._instrument_object.write_termination = (
#             "\0"  # Set PyVISA write terminator
#         )
#         self.k4200._instrument_object.read_termination = "\r\n"

#     def __del__(self):
#         self.k4200.disconnect()

#     def configure(self, options={}):
#         if "frequency" in options.keys():
#             frequency = options["frequency"]
#         else:
#             frequency = 1e5

#         self.frequency = frequency

#         if "ac_terminal" in options.keys():
#             ac_terminal = options["ac_terminal"]
#         else:
#             ac_terminal = 1

#         if "acv" in options.keys():
#             acv = options["acv"]
#         else:
#             acv = 1.0

#         if "dc_bias" in options.keys():
#             dcv = options["dc_bias"]
#             soakv = options["dc_bias"]
#             dcv_offset = options["dc_bias"]
#         else:
#             dcv = -10
#             soakv = -10
#             dcv_offset = -10

#         self.k4200.write(":CVU:MODE 0")
#         # self.k4200.write(":CVU:STANDBY 0")
#         self.k4200.write(":CVU:LENGTH 1.5")
#         self.k4200.write(":CVU:CORRECT 0,0,0")
#         self.k4200.write(":CVU:CONFIG:ACVHI " + str(ac_terminal))
#         self.k4200.write(":CVU:CONFIG:DCVHI 2")
#         self.k4200.write(":CVU:ACV " + str(acv))
#         # self.k4200.write(":CVU:ACZ:RANGE 1e-6")
#         self.k4200.write(":CVU:ACZ:RANGE 0")

#         self.k4200.write(":CVU:MODEL 1")
#         self.k4200.write(":CVU:SPEED 3,1,3,10")
#         # self.k4200.write(":CVU:SPEED 2")

#         self.k4200.write(":CVU:DCV:OFFSET " + str(dcv_offset))
#         self.k4200.write(":CVU:DCV " + str(dcv))
#         # self.k4200.write(":CVU:SOAK:DCV " + str(soakv))
#         # self.k4200.write(":CVU:DELAY:STEP 0.1")
#         # self.k4200.write(":CVU:TEST:RUN")
#         # self.k4200.write(
#         #     ":CVU:SWEEP:FREQ " + str(frequency) + "," + str(frequency) + ",1"
#         # )
#         # self.k4200.write(
#         #     ":CVU:STEP:FREQ " + str(frequency) + "," + str(frequency)
#         # )
#         # self.k4200.write(":CVU:DELAY:SWEEP 0")

#         self.k4200.write(":CVU:FREQ " + str(frequency))
#         # self.k4200.write(":CVU:MODE 0")
#         # time.sleep(0.5)
#         # while self.k4200._instrument_object.stb not in [0, 1]:
#         #     print(
#         #         "Waiting on measurement, status : ", self.k4200._instrument_object.stb
#         #     )
#         #     time.sleep(0.25)

#         # response_FREQ = (
#         #     self.k4200.query(":CVU:DATA:FREQ?").replace("\x00", "").replace("ACK", "")
#         # )
#         # frequencies = np.array(response_FREQ.split(",")[:-1], dtype=float)

#     def measure_Z(self):

#         # self.k4200.write(":CVU:TEST:RUN")

#         # response_Z = self.k4200.query(":CVU:DATA:Z?").replace("\x00", "").replace("ACK", "")
#         time.sleep(5)
#         response_Z = (
#             self.k4200.query(":CVU:MEASZ?").replace("\x00", "").replace("ACK", "")
#         )

#         Z = np.array(response_Z.split(","), dtype=float)
#         Z = Z[0] + 1j * Z[1]

#         return self.frequency, Z
