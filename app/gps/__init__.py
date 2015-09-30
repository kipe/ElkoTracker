from math import floor, isinf
import constants
import json

import os
import threading
import serial


class Datetime(object):
    year = 0
    month = 1
    day = 1

    hour = 0
    minute = 0
    second = 0
    millisecond = 0

    def __repr__(self):
        return self.to_iso()

    def parse_date(self, s):
        self.day, self.month, self.year = [int(s[i:i + 2]) for i in range(0, len(s), 2)]

    def parse_time(self, s):
        if '.' in s:
            s = s.split('.')
            self.millisecond = int(s[1])
            s = s[0]
        self.hour, self.minute, self.second = [int(s[i:i + 2]) for i in range(0, len(s), 2)]

    def to_iso(self):
        return '%04d-%02d-%02dT%02d:%02d:%02d.%03dZ' % (
            self.year + 2000,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            self.millisecond,
        )


class GPS(object):
    fix = constants.NO_FIX
    time = Datetime()
    latitude = 61.065643
    longitude = 28.093524
    # In m/s
    speed = 0
    satellites = []
    altitude = 0
    heading = 0
    pdop = float('inf')
    hdop = float('inf')
    vdop = float('inf')

    state = constants.MSG_WAITING
    msg_buffer = ''
    supported_sentences = ['RMC', 'GSA', 'GGA', 'GLL', 'VTG']

    def __repr__(self):
        return {
            'fix': self.fix,
            'time': self.time.to_iso(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'speed': self.speed,
            'heading': self.heading,
            'altitude': self.altitude,
            'satellites': self.satellites,
            'pdop': -1 if isinf(self.pdop) else self.pdop,
            'hdop': -1 if isinf(self.hdop) else self.hdop,
            'vdop': -1 if isinf(self.vdop) else self.vdop,
        }

    def _parse_degrees(self, s, d):
        s = float(s)
        l = float(int(floor(s / 100)) + (s / 100 - int(floor(s / 100))) / 60 * 100)
        if d in ['S', 'W']:
            return -l
        return l

    def _parse_rmc(self, data):
        if data[2] == 'V':
            self.fix = constants.NO_FIX
        elif self.fix == constants.NO_FIX:
            self.fix = constants.FIX_2D

        self.time.parse_time(data[1])
        self.time.parse_date(data[9])
        # self.latitude = self._parse_degrees(data[3], data[4])
        # self.longitude = self._parse_degrees(data[5], data[6])
        self.speed = float(data[7]) * constants.KNOTS_TO_MS
        self.heading = float(data[8])

    def _parse_gsa(self, data):
        if data[2] == '2':
            self.fix = constants.FIX_2D
        elif data[2] == '3':
            self.fix = constants.FIX_3D
        else:
            self.fix = constants.NO_FIX

        self.satellites = [int(x) for x in data[3:15] if x]
        self.pdop = float(data[15])
        self.hdop = float(data[16])
        self.vdop = float(data[17])

    def _parse_gga(self, data):
        print(data)
        self.time.parse_time(data[1])
        # self.latitude = self._parse_degrees(data[2], data[3])
        # self.longitude = self._parse_degrees(data[4], data[5])

        f = int(data[6])
        # If fix is invalid -> reset to invalid
        if f == 0:
            self.fix = constants.NO_FIX
        # else, we don't care about anything other than DGPS
        elif f == constants.FIX_DGPS:
            self.fix = constants.FIX_DGPS

        self.satellites = int(data[7])
        self.altitude = float(data[9])

    def _parse_gll(self, data):
        # self.latitude = self._parse_degrees(data[1], data[2])
        # self.longitude = self._parse_degrees(data[3], data[4])
        self.time.parse_time(data[5])
        if data[6] != 'A':
            self.fix = constants.NO_FIX

    def _parse_vtg(self, data):
        self.heading = float(data[1])
        self.speed = float(data[5]) * constants.KNOTS_TO_MS

    def recv(self, c):
        # If we're waiting for new message, but the character isn't start char
        # -> skip
        if c != '$' and self.state == constants.MSG_WAITING:
            return

        if c == '$' and self.state == constants.MSG_WAITING:
            self.state = constants.MSG_IN_PROGRESS
            self.msg_buffer += c
            return

        # If char is new line (indicating end of message)
        # and state is in progress
        if c in ['\r', '\n'] and self.state == constants.MSG_IN_PROGRESS:
            # parse message
            self.parse(self.msg_buffer)
            # clear buffer
            self.msg_buffer = ''
            # change state back to wait
            self.state = constants.MSG_WAITING
            return

        # Otherwise, add character to buffer
        self.msg_buffer += c

    def parse(self, msg):
        msg_type = msg[3:6]
        if msg_type not in self.supported_sentences:
            return

        msg_crc = int(msg[-2:], 16)
        crc = 0
        for c in msg[1:-3]:
            crc ^= ord(c)

        # if CRC doesn't match, ignore
        if crc != msg_crc:
            return

        msg = msg[0:-3].split(',')
        if msg_type == 'RMC':
            return self._parse_rmc(msg)
        if msg_type == 'GSA':
            return self._parse_gsa(msg)
        if msg_type == 'GGA':
            return self._parse_gga(msg)
        if msg_type == 'GLL':
            return self._parse_gll(msg)
        if msg_type == 'VTG':
            return self._parse_vtg(msg)

    def json(self):
        return json.dumps(self.__repr__())


class SerialGPS(GPS, threading.Thread):
    def __init__(self):
        self.serial = None
        self._stop = threading.Event()

        GPS.__init__(self)
        threading.Thread.__init__(self)

    def run(self):
        self.open_port()
        while not self._stop.is_set():
            self.recv(self.serial.read())

    def stop(self):
        self._stop.set()
        if self.serial is not None:
            self.serial.close()

    def open_port(self):
        if self.serial is not None and not self.serial.closed:
            self.serial.close()

        self.serial = serial.Serial(
            os.environ.get('SERIAL_PORT', '/dev/ttyUSB0'),
            timeout=1,
            baudrate=int(os.environ.get('SERIAL_BAUDRATE', 115200)),
        )


if __name__ == '__main__':
    import time

    gps = SerialGPS()
    gps.start()
    while True:
        try:
            print(gps)
            time.sleep(1)
        except KeyboardInterrupt:
            break
    gps.stop()
