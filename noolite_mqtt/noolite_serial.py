#!/usr/bin/python3

import serial


class NooLiteCommand:
    def __init__(self, ch, cmd, mode=0, ctr=0, res=0, fmt=0, d0=0, d1=0, d2=0, d3=0, id0=0, id1=0, id2=0, id3=0):
        self.st = 171
        self.mode = mode
        self.ctr = ctr
        self.res = res
        self.ch = ch
        self.cmd = cmd
        self.fmt = fmt
        self.d0 = d0
        self.d1 = d1
        self.d2 = d2
        self.d3 = d3
        self.id0 = id0
        self.id1 = id1
        self.id2 = id2
        self.id3 = id3
        self.sp = 172

    @property
    def crc(self):
        crc = sum([
            self.st,
            self.mode,
            self.ctr,
            self.res,
            self.ch,
            self.cmd,
            self.fmt,
            self.d0,
            self.d1,
            self.d2,
            self.d3,
            self.id0,
            self.id1,
            self.id2,
            self.id3,
        ])
        return crc if crc < 256 else divmod(crc, 256)[1]

    def to_bytes(self):
        return bytearray([
            self.st,
            self.mode,
            self.ctr,
            self.res,
            self.ch,
            self.cmd,
            self.fmt,
            self.d0,
            self.d1,
            self.d2,
            self.d3,
            self.id0,
            self.id1,
            self.id2,
            self.id3,
            self.crc,
            self.sp
        ])


class NooLiteSerial:
    def __init__(self, tty_name):
        self.tty = self._get_tty(tty_name)

    def on(self, ch):
        self.send_command(ch, 2, 2, 0)
        pass

    def off(self, ch):
        self.send_command(ch, 0, 2, 0)
        pass

    def status(self, ch):
        self.send_command(ch, 128, 2, 0)
        pass

    def send_command(self, ch, cmd, mode=0, ctr=0, res=0, fmt=0, d0=0, d1=0, d2=0, d3=0, id0=0, id1=0, id2=0, id3=0):
        command = NooLiteCommand(ch, cmd, mode, ctr, res, fmt, d0, d1, d2, d3, id0, id1, id2, id3)
        self.tty.write(command.to_bytes())
        pass

    def receive(self):
        all_responses = list()
        while self.tty.inWaiting() >= 17:
            bytes_response = list(self.tty.read(17))
            if bytes_response:
                all_responses.append(bytes_response)
                if bytes_response[3] == 0:
                    break
            else:
                break
        return all_responses

    @staticmethod
    def _get_tty(tty_name):
        serial_port = serial.Serial(tty_name, 9600, timeout=0.1)
        if not serial_port.isOpen():
            serial_port.open()
        serial_port.flushInput()
        serial_port.flushOutput()
        return serial_port
