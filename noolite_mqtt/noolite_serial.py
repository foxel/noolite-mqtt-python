import serial

from .enums import Command, Mode, Request


class NooLiteCommand:
    def __init__(
            self,
            ch: int,
            cmd: Command,
            mode: Mode = Mode.TX,
            ctr: Request = Request.CMD,
            fmt: int = 0,
            d0: int = 0, d1: int = 0, d2: int = 0, d3: int = 0,
            id0: int = 0, id1: int = 0, id2: int = 0, id3: int = 0
    ):
        self.st = 171
        self.mode = mode
        self.ctr = ctr
        self.res = 0
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

    def on(self, ch, noolite_f: bool = False):
        self.send_command(ch, Command.ON, Mode.TX_F if noolite_f else Mode.TX, Request.CMD)
        pass

    def off(self, ch, noolite_f: bool = False):
        self.send_command(ch, Command.OFF, Mode.TX_F if noolite_f else Mode.TX, Request.CMD)
        pass

    def status(self, ch):
        self.send_command(ch, Command.READ_STATE, Mode.TX_F, Request.CMD)
        pass

    def send_command(
            self,
            ch: int,
            cmd: Command,
            mode: Mode = Mode.TX,
            ctr: Request = Request.CMD,
            fmt: int = 0,
            d0: int = 0, d1: int = 0, d2: int = 0, d3: int = 0,
            id0: int = 0, id1: int = 0, id2: int = 0, id3: int = 0
    ):
        command = NooLiteCommand(ch, cmd, mode, ctr, fmt, d0, d1, d2, d3, id0, id1, id2, id3)
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
