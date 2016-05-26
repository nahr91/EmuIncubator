import Adafruit_BBIO.GPIO as GPIO
from time import sleep

LOW = 0
HIGH =1
LSBFIRST = 1
MSBFIRST = 0
global SHT15_SCK_LO
global SHT15_SCK_HI
global SHT15_DATA_LO
global SHT15_DATA_HI
global SHT15_GET_BIT
global SHT15_SENT_BIT

DATA = 'P8_16'
SCK = 'P8_15'

class BB_SHT15:
    """
    SHT10, SHT11 and SHT15 humidity and temperature sensor class.
    :param data_pin: GPIO pin connected to DATA line.
    :type data_pin: :class:`IoTPy.pyuper.gpio.GPIO`
    :param clk_pin: GPIO pin connected to SCK line.
    :type clk_pin: :class:`IoTPy.pyuper.gpio.GPIO`
    """

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, traceback):
        pass

    def SHT15_SCK_LO(self):
	GPIO.setup(SCK, GPIO.OUT)
	GPIO.output(SCK, GPIO.LOW)
        GPIO.cleanup()

    def SHT15_SCK_HI(self):
	GPIO.setup(SCK, GPIO.OUT)
        GPIO.output(SCK, GPIO.HIGH)
        GPIO.cleanup()

    def SHT15_DATA_LO(self):
        GPIO.setup(DATA, GPIO.OUT)
        GPIO.output(DATA, GPIO.LOW)
        GPIO.cleanup()

    def SHT15_DATA_HI(self):
        GPIO.setup(DATA, GPIO.OUT)
        GPIO.output(DATA, GPIO.HIGH)
        GPIO.cleanup()

    def SHT15_GET_BIT(self):
        GPIO.setup(DATA, GPIO.IN)
        RX = GPIO.input(DATA)
        return(RX)

    def SHT15_SENT_BIT(self, TX):
        GPIO.setup(DATA, GPIO.OUT)
        GPIO.output(DATA, TX)
	GPIO.cleanup()

    def _shift_out(self, bit_order, byte, bits):
        for i in xrange(bits):
            if bit_order == LSBFIRST:
                self.SHT15_SENT_BIT(byte & (1 << i))
            else:
                self.SHT15_SENT_BIT(byte & (1 << (7 -i)))
            self.SHT15_SCK_HI()
            sleep(0.0003)
            self.SHT15_SCK_LO()

    def _sht_command(self, command):
	self.SHT15_DATA_HI()
        self.SHT15_SCK_HI()
        self.SHT15_DATA_LO()
	self.SHT15_SCK_LO()
        self.SHT15_SCK_HI()
	self.SHT15_DATA_HI()
	self.SHT15_SCK_LO()
        self.SHT15_DATA_LO()

        self._shift_out(MSBFIRST, command, 8)
        self.SHT15_SCK_HI()
        ack = self.SHT15_GET_BIT()
        if ack != LOW:
            raise RuntimeError("No ACK. Sensor not present?")
        self.SHT15_SCK_LO()
        ack = self.SHT15_GET_BIT()
        if ack != HIGH:
            raise RuntimeError("No ACK. Sensor not present?")

    def _shift_in(self, bits):
        ret = 0
        for i in xrange(bits):
            self.SHT15_SCK_HI()
            sleep(0.01)
            ret = (ret << 1) + self.SHT15_GET_BIT()
            self.SHT15_SCK_LO()
        return ret

    def _wait_sht(self):
        for i in xrange(100):
            sleep(0.002)
            ack = self.SHT15_GET_BIT()
            if ack == LOW:
                break
        if ack == HIGH:
            raise RuntimeError("Measurement wait timeout")

    def _get_data_sht(self):
        val = self._shift_in(8) * 256
	self.SHT15_DATA_HI()
	self.SHT15_DATA_LO()
        self.SHT15_SCK_HI()
        self.SHT15_SCK_LO()
        val |= self._shift_in(8)
        return val

    def _skip_crc(self):
	self.SHT15_DATA_HI()
        self.SHT15_SCK_HI()
        self.SHT15_SCK_LO()

    def _temperature_raw(self):
        self._sht_command(0x03)
        self._wait_sht()
        val = self._get_data_sht()
        self._skip_crc()
        return val

    def temperature(self):
        """
        Measure and return temperature.
        :return: A measured temperature in celsius.
        :rtype: int
        """
        return(self._temperature_raw() * 0.01) - 40.1

    def humidity(self):
        """
        Measure and return humidity.
        :return: A measured humidity value in percents.
        :rtype: int
        """

        """
        C1 = -4.0       # for 12 Bit
        C2 =  0.0405    # for 12 Bit
        C3 = -0.0000028 # for 12 Bit
        T1 =  0.01      # for 14 Bit @ 5V
        T2 =  0.00008   # for 14 Bit @ 5V
        """
        C1 = -2.0468       # for 12 Bit
        C2 =  0.0367    # for 12 Bit
        C3 = -0.0000015955 # for 12 Bit
        T1 =  0.01      # for 14 Bit @ 5V
        T2 =  0.00008   # for 14 Bit @ 5V

        self._sht_command(0x05)
        self._wait_sht()
        val = self._get_data_sht()
        self._skip_crc()
        linear_humidity = C1 + C2 * val + C3 * val * val
	return((self.temperature() - 25.0 ) * (T1 + T2 * val) + linear_humidity)

